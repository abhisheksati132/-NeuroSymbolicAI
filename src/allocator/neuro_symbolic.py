"""
Neuro-Symbolic Cloud Resource Allocator.
Synthesizes deep neural sequence demand forecasting with explicit symbolic
constraint reasoning and rule-trace explainability.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from src.simulator.host import Host
from src.simulator.task import Task
from src.symbolic.rules import SymbolicRuleEngine
from src.allocator.base_allocator import BaseAllocator


class NeuroSymbolicAllocator(BaseAllocator):
    """
    Proposed Neuro-Symbolic Allocator:
    1. Neural Forecaster predicts cluster demand trend across upcoming time horizon.
    2. Proactive scale-out / headroom reservation triggered when forecast exceeds threshold.
    3. Symbolic Rule Engine validates candidate hosts against hard safety and affinity constraints.
    4. Any candidate violating hard rules is rejected and re-planned.
    5. Detailed explainable rule audit log generated for every decision.
    """
    def __init__(self, forecaster: Any, saturation_threshold: float = 0.75):
        super().__init__("Neuro-Symbolic")
        self.forecaster = forecaster
        self.rule_engine = SymbolicRuleEngine(
            max_capacity_threshold=0.85,
            high_priority_headroom_threshold=0.75,
        )
        self.saturation_threshold = saturation_threshold

    def allocate(self, task: Task, hosts: List[Host], env: Any = None) -> Dict[str, Any]:
        # 1. Neural Forecast Phase
        pred_cpu, pred_ram = 0.0, 0.0
        forecasted_saturation = False

        if env and len(env.step_history) >= 12:
            hist = np.array([
                [h["cpu_util"] * env.total_cpu_capacity, h["ram_util"] * env.total_ram_capacity]
                for h in env.step_history[-12:]
            ])
            pred_cpu, pred_ram = self.forecaster.predict_next(hist)

            active_cpu_cap = sum(h.cpu_capacity for h in hosts if h.is_active)
            active_ram_cap = sum(h.ram_capacity for h in hosts if h.is_active)
            
            if active_cpu_cap > 0 and (pred_cpu / active_cpu_cap) > self.saturation_threshold:
                forecasted_saturation = True
            elif active_ram_cap > 0 and (pred_ram / active_ram_cap) > self.saturation_threshold:
                forecasted_saturation = True

        # 2. Candidate Generation & Symbolic Evaluation Phase
        evaluated_candidates = []
        for host in hosts:
            admissible, score, evals = self.rule_engine.evaluate_host_candidate(
                task, host, forecasted_saturation=forecasted_saturation
            )
            evaluated_candidates.append({
                "host": host,
                "admissible": admissible,
                "score": score,
                "evals": evals,
            })

        # Filter only admissible candidates (strictly satisfying R1, R2, R3)
        admissible_candidates = [c for c in evaluated_candidates if c["admissible"]]

        if admissible_candidates:
            # Sort by combined symbolic + neural preference score descending
            admissible_candidates.sort(key=lambda x: x["score"], reverse=True)
            winner = admissible_candidates[0]
            chosen_host = winner["host"]

            eval_summary = "; ".join(f"{e.rule_id}:{e.reason}" for e in winner["evals"] if not e.is_hard or e.passed)
            rejection_count = len(evaluated_candidates) - len(admissible_candidates)

            trace_msg = (
                f"Selected {chosen_host.host_id} (score={winner['score']:.1f}, "
                f"forecast_sat={forecasted_saturation}, pred_cpu={pred_cpu:.1f}). "
                f"Admissible: {len(admissible_candidates)}/{len(hosts)}, Rejections: {rejection_count}. "
                f"Trace: [{eval_summary}]"
            )

            return {
                "target_host_id": chosen_host.host_id,
                "trace": trace_msg,
                "hard_rule_violated": False,
            }

        # 3. Re-planning / Fallback
        # If no host is admissible under strict rules, look for an idle standby host to power on
        standby_hosts = [h for h in hosts if not h.is_active]
        for sb in standby_hosts:
            if sb.can_fit(task.cpu_req, task.ram_req, max_threshold=0.85):
                # Safe to power on
                return {
                    "target_host_id": sb.host_id,
                    "trace": f"Re-planning: Powered on standby {sb.host_id} after all active hosts were rejected by safety rules.",
                    "hard_rule_violated": False,
                }

        # Last resort: task must wait in queue rather than causing a dangerous hard-rule breach
        reasons = [f"{c['host'].host_id}: {[e.reason for e in c['evals'] if not e.passed]}" for c in evaluated_candidates]
        trace_msg = f"Task deferred to queue: No host passed hard constraints. Rejection audits: {reasons[:3]}"
        return {
            "target_host_id": None,
            "trace": trace_msg,
            "hard_rule_violated": False,
        }
