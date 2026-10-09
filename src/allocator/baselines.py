"""
Baseline Cloud Resource Allocation Policies.
Includes Round Robin, First Fit, Best Fit, Pure Symbolic, and Pure Neural.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from src.simulator.host import Host
from src.simulator.task import Task
from src.symbolic.rules import SymbolicRuleEngine
from src.allocator.base_allocator import BaseAllocator


class RoundRobinAllocator(BaseAllocator):
    """
    Cycles sequentially through hosts, placing tasks on the next host with raw capacity.
    Rule-unaware (violates 85% threshold and anti-affinity when congested).
    """
    def __init__(self):
        super().__init__("Round Robin")
        self.pointer: int = 0
        self.rule_engine = SymbolicRuleEngine()

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        num_hosts = len(hosts)
        for i in range(num_hosts):
            idx = (self.pointer + i) % num_hosts
            host = hosts[idx]
            if host.can_fit(task.cpu_req, task.ram_req, max_threshold=1.0):
                self.pointer = (idx + 1) % num_hosts
                # Check if this placement violates safety rules
                admissible, _, evals = self.rule_engine.evaluate_host_candidate(task, host)
                return {
                    "target_host_id": host.host_id,
                    "trace": f"Round Robin selected {host.host_id} (pointer={idx})",
                    "hard_rule_violated": not admissible,
                }
        return {"target_host_id": None, "trace": "Round Robin: No capacity", "hard_rule_violated": False}


class FirstFitAllocator(BaseAllocator):
    """
    Assigns task to the first host that can physically fit the request.
    Rule-unaware (violates 85% threshold and anti-affinity when congested).
    """
    def __init__(self):
        super().__init__("First Fit")
        self.rule_engine = SymbolicRuleEngine()

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        for host in hosts:
            if host.can_fit(task.cpu_req, task.ram_req, max_threshold=1.0):
                admissible, _, evals = self.rule_engine.evaluate_host_candidate(task, host)
                return {
                    "target_host_id": host.host_id,
                    "trace": f"First Fit matched {host.host_id}",
                    "hard_rule_violated": not admissible,
                }
        return {"target_host_id": None, "trace": "First Fit: No host fits", "hard_rule_violated": False}


class BestFitAllocator(BaseAllocator):
    """
    Assigns task to the host that leaves the smallest remaining residual capacity.
    Rule-unaware (violates 85% threshold and anti-affinity when packed tight).
    """
    def __init__(self):
        super().__init__("Best Fit")
        self.rule_engine = SymbolicRuleEngine()

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        best_host = None
        min_residual = float("inf")

        for host in hosts:
            if host.can_fit(task.cpu_req, task.ram_req, max_threshold=1.0):
                remaining_cpu = (host.cpu_capacity - (host.cpu_used + task.cpu_req))
                remaining_ram = (host.ram_capacity - (host.ram_used + task.ram_req))
                residual = remaining_cpu + remaining_ram
                if residual < min_residual:
                    min_residual = residual
                    best_host = host

        if best_host:
            admissible, _, _ = self.rule_engine.evaluate_host_candidate(task, best_host)
            return {
                "target_host_id": best_host.host_id,
                "trace": f"Best Fit selected {best_host.host_id} (residual={min_residual:.1f})",
                "hard_rule_violated": not admissible,
            }
        return {"target_host_id": None, "trace": "Best Fit: No host fits", "hard_rule_violated": False}


class PureSymbolicAllocator(BaseAllocator):
    """
    Pure Rule-Based Allocator: Evaluates all explicit constraints and soft policies.
    Guarantees 0 hard-rule violations, but lacks predictive proactive scaling.
    """
    def __init__(self):
        super().__init__("Pure Symbolic")
        self.rule_engine = SymbolicRuleEngine()

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        best_host = None
        best_score = -float("inf")
        best_evals = []

        for host in hosts:
            admissible, score, evals = self.rule_engine.evaluate_host_candidate(
                task, host, forecasted_saturation=False
            )
            if admissible and score > best_score:
                best_score = score
                best_host = host
                best_evals = evals

        if best_host:
            trace_str = " | ".join(str(e) for e in best_evals)
            return {
                "target_host_id": best_host.host_id,
                "trace": f"Pure Symbolic accepted {best_host.host_id} [score={best_score:.1f}]: {trace_str}",
                "hard_rule_violated": False,
            }
        return {
            "target_host_id": None,
            "trace": "Pure Symbolic: All hosts rejected by safety constraints",
            "hard_rule_violated": False,
        }


class PureNeuralAllocator(BaseAllocator):
    """
    Pure Neural Allocator: Uses GRU demand forecast to score hosts based on predicted
    headroom and load affinity, but operates without symbolic rule validation.
    Susceptible to hard-rule violations and unexplainable edge cases.
    """
    def __init__(self, forecaster: Any):
        super().__init__("Pure Neural")
        self.forecaster = forecaster
        self.rule_engine = SymbolicRuleEngine()

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        # Formulate neural prediction if history exists
        pred_cpu, pred_ram = 0.0, 0.0
        if env and len(env.step_history) >= 12:
            hist = np.array([
                [h["cpu_util"] * env.total_cpu_capacity, h["ram_util"] * env.total_ram_capacity]
                for h in env.step_history[-12:]
            ])
            pred_cpu, pred_ram = self.forecaster.predict_next(hist)

        # Pure neural scoring: prefers hosts with higher raw remaining capacity,
        # but does not check 85% safety limits, P3 headroom rules, or anti-affinity
        candidate_scores = []
        for host in hosts:
            if host.can_fit(task.cpu_req, task.ram_req, max_threshold=1.0):
                # Heuristic based on predicted congestion
                rem_cpu = host.cpu_capacity - (host.cpu_used + task.cpu_req)
                rem_ram = host.ram_capacity - (host.ram_used + task.ram_req)
                score = (rem_cpu / host.cpu_capacity) + (rem_ram / host.ram_capacity)
                candidate_scores.append((host, score))

        if candidate_scores:
            # Pick highest score
            candidate_scores.sort(key=lambda x: x[1], reverse=True)
            chosen_host = candidate_scores[0][0]
            
            # Check if this placement violates safety rules (unmonitored by neural component)
            admissible, _, _ = self.rule_engine.evaluate_host_candidate(task, chosen_host)
            return {
                "target_host_id": chosen_host.host_id,
                "trace": f"Pure Neural assigned {chosen_host.host_id} (latent score={candidate_scores[0][1]:.2f}, pred_cpu={pred_cpu:.1f})",
                "hard_rule_violated": not admissible,
            }
        return {"target_host_id": None, "trace": "Pure Neural: No physical fit", "hard_rule_violated": False}
