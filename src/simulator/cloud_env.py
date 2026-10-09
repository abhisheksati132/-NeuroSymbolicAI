"""
Cloud Datacenter Discrete-Time Simulation Environment.
Coordinates heterogeneous hosts, workload arrival queues, power accounting,
and allocator dispatch loops.
"""
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from src.simulator.host import Host
from src.simulator.task import Task


def create_default_heterogeneous_cluster(num_hosts: int = 12) -> List[Host]:
    """
    Constructs a heterogeneous server cluster with standard host types:
    - General Purpose (GP-4): 16 vCPU, 64 GB RAM
    - Compute Optimized (CO-4): 32 vCPU, 64 GB RAM
    - Memory Optimized (MO-4): 16 vCPU, 128 GB RAM
    """
    hosts = []
    types_config = [
        ("GP-4", 16.0, 64.0, 80.0, 250.0, 10.0, 0.40),
        ("CO-4", 32.0, 64.0, 110.0, 380.0, 12.0, 0.65),
        ("MO-4", 16.0, 128.0, 95.0, 310.0, 12.0, 0.75),
    ]
    for i in range(num_hosts):
        h_type, cpu, ram, p_idle, p_peak, p_standby, cost = types_config[i % len(types_config)]
        host = Host(
            host_id=f"host_{i:02d}",
            host_type=h_type,
            cpu_capacity=cpu,
            ram_capacity=ram,
            p_idle=p_idle,
            p_peak=p_peak,
            p_standby=p_standby,
            cost_per_hour=cost,
        )
        hosts.append(host)
    return hosts


class CloudEnvironment:
    """
    Discrete-time simulator for cloud datacenter resource management.
    """
    def __init__(
        self,
        hosts: Optional[List[Host]] = None,
        time_step_seconds: float = 60.0,
    ):
        self.time_step_seconds = time_step_seconds
        self.hosts: List[Host] = hosts if hosts is not None else create_default_heterogeneous_cluster()
        self.current_step: int = 0
        self.pending_queue: List[Task] = []
        self.active_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        
        # Scale events counter
        self.scale_events: int = 0
        self.last_active_host_ids = set()

        # Step-by-step history tracking
        self.step_history: List[Dict[str, Any]] = []

    def reset(self, hosts: Optional[List[Host]] = None) -> None:
        """Resets the environment to initial conditions."""
        self.hosts = hosts if hosts is not None else create_default_heterogeneous_cluster()
        self.current_step = 0
        self.pending_queue = []
        self.active_tasks = []
        self.completed_tasks = []
        self.scale_events = 0
        self.last_active_host_ids = set()
        self.step_history = []

    @property
    def total_cpu_capacity(self) -> float:
        return sum(h.cpu_capacity for h in self.hosts)

    @property
    def total_ram_capacity(self) -> float:
        return sum(h.ram_capacity for h in self.hosts)

    @property
    def total_cpu_used(self) -> float:
        return sum(h.cpu_used for h in self.hosts)

    @property
    def total_ram_used(self) -> float:
        return sum(h.ram_used for h in self.hosts)

    @property
    def cluster_cpu_utilization(self) -> float:
        cap = self.total_cpu_capacity
        return self.total_cpu_used / cap if cap > 0 else 0.0

    @property
    def cluster_ram_utilization(self) -> float:
        cap = self.total_ram_capacity
        return self.total_ram_used / cap if cap > 0 else 0.0

    @property
    def cluster_power_watts(self) -> float:
        return sum(h.current_power_watts for h in self.hosts)

    def run_simulation(
        self,
        tasks: List[Task],
        allocator: Any,
        time_horizon: int = 120,
    ) -> Dict[str, Any]:
        """
        Runs complete simulation across the specified workload tasks using the provided allocator.
        """
        self.reset()
        tasks_by_arrival: Dict[int, List[Task]] = {}
        for t in tasks:
            tasks_by_arrival.setdefault(t.arrival_time, []).append(t)

        decision_latencies: List[float] = []
        rule_traces_recorded: int = 0
        total_allocations: int = 0
        hard_rule_violations: int = 0

        for step in range(time_horizon):
            self.current_step = step
            
            # 1. Step active tasks and release completed ones
            still_active = []
            for task in self.active_tasks:
                finished = task.step(step)
                if finished:
                    # Release host capacity
                    if task.host_id:
                        host = next((h for h in self.hosts if h.host_id == task.host_id), None)
                        if host:
                            host.release(task.task_id)
                    self.completed_tasks.append(task)
                else:
                    still_active.append(task)
            self.active_tasks = still_active

            # 2. Add newly arrived tasks to pending queue
            new_tasks = tasks_by_arrival.get(step, [])
            self.pending_queue.extend(new_tasks)

            # Step pending tasks (increment waiting time)
            for pt in self.pending_queue:
                pt.step(step)

            # 3. Allocator step: attempt placement of queued tasks
            unplaced = []
            while self.pending_queue:
                task_to_place = self.pending_queue.pop(0)
                t_start = time.perf_counter()
                
                # Allocator decides target host
                decision = allocator.allocate(task_to_place, self.hosts, env=self)
                latency_ms = (time.perf_counter() - t_start) * 1000.0
                decision_latencies.append(latency_ms)
                total_allocations += 1

                target_host_id = decision.get("target_host_id")
                trace = decision.get("trace", "")
                is_rule_violated = decision.get("hard_rule_violated", False)
                
                if trace:
                    rule_traces_recorded += 1
                if is_rule_violated:
                    hard_rule_violations += 1
                    task_to_place.hard_rule_violated = True

                if target_host_id:
                    host = next((h for h in self.hosts if h.host_id == target_host_id), None)
                    if host and host.allocate(task_to_place):
                        task_to_place.allocated = True
                        task_to_place.start_time = step
                        self.active_tasks.append(task_to_place)
                    else:
                        unplaced.append(task_to_place)
                else:
                    unplaced.append(task_to_place)

            self.pending_queue = unplaced

            # 4. Check for scale events (new active hosts)
            current_active_hosts = {h.host_id for h in self.hosts if h.is_active}
            newly_activated = current_active_hosts - self.last_active_host_ids
            self.scale_events += len(newly_activated)
            self.last_active_host_ids = current_active_hosts

            # 5. Accumulate energy and step hosts
            for host in self.hosts:
                host.step(self.time_step_seconds)

            # Record metrics history
            self.step_history.append({
                "step": step,
                "cpu_util": self.cluster_cpu_utilization,
                "ram_util": self.cluster_ram_utilization,
                "power_watts": self.cluster_power_watts,
                "active_hosts": len(current_active_hosts),
                "active_tasks": len(self.active_tasks),
                "pending_tasks": len(self.pending_queue),
            })

        # Finish remaining active tasks at end of horizon
        for t in self.active_tasks:
            t.sla_violated = True
            self.completed_tasks.append(t)
        for t in self.pending_queue:
            t.sla_violated = True
            self.completed_tasks.append(t)

        # Compute summary metrics
        all_simulated_tasks = self.completed_tasks
        total_tasks_count = len(all_simulated_tasks)
        sla_violated_count = sum(1 for t in all_simulated_tasks if t.sla_violated)
        sla_violation_rate = (sla_violated_count / total_tasks_count * 100.0) if total_tasks_count > 0 else 0.0

        avg_waiting = float(np.mean([t.waiting_time for t in all_simulated_tasks])) if all_simulated_tasks else 0.0
        total_energy_kwh = sum(h.total_energy_joules for h in self.hosts) / 3.6e6
        
        # Calculate cost based on active host-hours
        total_cost_usd = sum(
            h.cost_per_hour * (h.total_active_seconds / 3600.0)
            for h in self.hosts
        )

        hist_df = pd.DataFrame(self.step_history)
        avg_cpu_util = float(hist_df["cpu_util"].mean()) if not hist_df.empty else 0.0
        avg_ram_util = float(hist_df["ram_util"].mean()) if not hist_df.empty else 0.0
        avg_decision_ms = float(np.mean(decision_latencies)) if decision_latencies else 0.0
        explainability_pct = (rule_traces_recorded / total_allocations * 100.0) if total_allocations > 0 else 0.0

        return {
            "avg_cpu_utilization": avg_cpu_util,
            "avg_ram_utilization": avg_ram_util,
            "sla_violation_rate": sla_violation_rate,
            "sla_violated_count": sla_violated_count,
            "hard_rule_violations": hard_rule_violations,
            "avg_waiting_time": avg_waiting,
            "total_energy_kwh": total_energy_kwh,
            "total_cost_usd": total_cost_usd,
            "scale_events": self.scale_events,
            "avg_decision_time_ms": avg_decision_ms,
            "explainability_pct": explainability_pct,
            "history_df": hist_df,
            "total_tasks": total_tasks_count,
        }
