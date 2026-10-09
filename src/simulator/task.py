"""
Task/Request model for Cloud Datacenter Simulator.
Represents individual computational requests with CPU/RAM requirements,
priorities, deadlines, and SLA constraints.
"""
from typing import Optional, Dict, Any


class Task:
    """
    Represents an incoming computational task or workload container.
    """
    def __init__(
        self,
        task_id: str,
        tenant_id: str,
        cpu_req: float,
        ram_req: float,
        duration: int,
        priority: int = 1,
        arrival_time: int = 0,
        max_wait_tolerance: int = 5,
    ):
        self.task_id = task_id
        self.tenant_id = tenant_id
        self.cpu_req = float(cpu_req)
        self.ram_req = float(ram_req)
        self.duration = int(duration)
        self.remaining_time = int(duration)
        self.priority = int(priority)  # 1: Low (Batch), 2: Normal (Web), 3: High (Mission Critical)
        self.arrival_time = int(arrival_time)
        self.max_wait_tolerance = int(max_wait_tolerance)
        self.sla_deadline = self.arrival_time + self.max_wait_tolerance + self.duration

        # Dynamic state
        self.start_time: Optional[int] = None
        self.finish_time: Optional[int] = None
        self.host_id: Optional[str] = None
        self.waiting_time: int = 0
        self.sla_violated: bool = False
        self.hard_rule_violated: bool = False
        self.allocated: bool = False

    def step(self, current_time: int) -> bool:
        """
        Advances the task clock by 1 step.
        Returns True if task has finished execution.
        """
        if not self.allocated:
            self.waiting_time += 1
            if self.waiting_time > self.max_wait_tolerance:
                self.sla_violated = True
            return False

        if self.start_time is None:
            self.start_time = current_time

        self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.finish_time = current_time
            if self.finish_time > self.sla_deadline:
                self.sla_violated = True
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Dictionary representation of task state."""
        return {
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "cpu_req": self.cpu_req,
            "ram_req": self.ram_req,
            "duration": self.duration,
            "priority": self.priority,
            "arrival_time": self.arrival_time,
            "sla_deadline": self.sla_deadline,
            "start_time": self.start_time,
            "finish_time": self.finish_time,
            "host_id": self.host_id,
            "waiting_time": self.waiting_time,
            "sla_violated": self.sla_violated,
            "hard_rule_violated": self.hard_rule_violated,
        }
