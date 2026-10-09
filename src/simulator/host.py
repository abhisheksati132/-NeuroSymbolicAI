"""
Physical Host Model for Cloud Datacenter Simulator.
Implements resource tracking, power consumption models, and lifecycle states.
"""
from typing import Dict, Optional, Any


class Host:
    """
    Represents a heterogeneous physical cloud host.
    """
    def __init__(
        self,
        host_id: str,
        host_type: str,
        cpu_capacity: float,
        ram_capacity: float,
        p_idle: float = 80.0,
        p_peak: float = 250.0,
        p_standby: float = 10.0,
        cost_per_hour: float = 0.40,
    ):
        self.host_id = host_id
        self.host_type = host_type
        self.cpu_capacity = float(cpu_capacity)
        self.ram_capacity = float(ram_capacity)
        self.p_idle = float(p_idle)
        self.p_peak = float(p_peak)
        self.p_standby = float(p_standby)
        self.cost_per_hour = float(cost_per_hour)

        # State tracking
        self.is_active: bool = False  # True if host is powered on and ready/running
        self.cpu_used: float = 0.0
        self.ram_used: float = 0.0
        self.allocated_tasks: Dict[str, Any] = {}
        self.total_active_seconds: float = 0.0
        self.total_energy_joules: float = 0.0

    @property
    def cpu_utilization(self) -> float:
        """Current fractional CPU utilization in [0.0, 1.0]."""
        if self.cpu_capacity == 0:
            return 0.0
        return min(1.0, max(0.0, self.cpu_used / self.cpu_capacity))

    @property
    def ram_utilization(self) -> float:
        """Current fractional RAM utilization in [0.0, 1.0]."""
        if self.ram_capacity == 0:
            return 0.0
        return min(1.0, max(0.0, self.ram_used / self.ram_capacity))

    @property
    def dominant_utilization(self) -> float:
        """Max utilization between CPU and RAM for power computation."""
        return max(self.cpu_utilization, self.ram_utilization)

    @property
    def current_power_watts(self) -> float:
        """
        Calculates instantaneous power dissipation based on Fan et al. (ISCA 2007):
        P(u) = P_idle + (P_peak - P_idle) * max(u_cpu, u_ram) if active,
        else P_standby when consolidated/idle in standby.
        """
        if not self.is_active:
            return self.p_standby
        u = self.dominant_utilization
        return self.p_idle + (self.p_peak - self.p_idle) * u

    def can_fit(self, cpu_req: float, ram_req: float, max_threshold: float = 1.0) -> bool:
        """Checks if additional resource demand fits within a given threshold."""
        target_cpu = self.cpu_used + cpu_req
        target_ram = self.ram_used + ram_req
        return (target_cpu <= self.cpu_capacity * max_threshold) and (
            target_ram <= self.ram_capacity * max_threshold
        )

    def allocate(self, task: Any) -> bool:
        """Allocates a task to this host if feasible."""
        if not self.can_fit(task.cpu_req, task.ram_req, max_threshold=1.0):
            return False
        
        self.is_active = True
        self.allocated_tasks[task.task_id] = task
        self.cpu_used += task.cpu_req
        self.ram_used += task.ram_req
        task.host_id = self.host_id
        return True

    def release(self, task_id: str) -> Optional[Any]:
        """Releases an active task by its ID."""
        task = self.allocated_tasks.pop(task_id, None)
        if task:
            self.cpu_used = max(0.0, self.cpu_used - task.cpu_req)
            self.ram_used = max(0.0, self.ram_used - task.ram_req)
            task.host_id = None
            if len(self.allocated_tasks) == 0:
                # Idle host can transition to standby if consolidated
                self.cpu_used = 0.0
                self.ram_used = 0.0
        return task

    def step(self, delta_seconds: float = 60.0) -> None:
        """Advances host clock by delta_seconds, accumulating energy and active time."""
        power = self.current_power_watts
        self.total_energy_joules += power * delta_seconds
        if self.is_active:
            self.total_active_seconds += delta_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Returns host snapshot for monitoring."""
        return {
            "host_id": self.host_id,
            "host_type": self.host_type,
            "cpu_capacity": self.cpu_capacity,
            "ram_capacity": self.ram_capacity,
            "cpu_used": round(self.cpu_used, 2),
            "ram_used": round(self.ram_used, 2),
            "cpu_util": round(self.cpu_utilization, 4),
            "ram_util": round(self.ram_utilization, 4),
            "active_tasks_count": len(self.allocated_tasks),
            "is_active": self.is_active,
            "current_power_w": round(self.current_power_watts, 2),
            "cost_per_hour": self.cost_per_hour,
        }
