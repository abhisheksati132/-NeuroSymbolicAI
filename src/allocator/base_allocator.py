"""
Base Allocator Interface for Cloud Resource Management.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.simulator.host import Host
from src.simulator.task import Task


class BaseAllocator(ABC):
    """
    Abstract base class for datacenter resource allocation policies.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def allocate(
        self,
        task: Task,
        hosts: List[Host],
        env: Any = None
    ) -> Dict[str, Any]:
        """
        Determines target host for task placement.
        
        Returns:
            Dict containing:
                "target_host_id": Optional[str],
                "trace": Optional[str],
                "hard_rule_violated": bool
        """
        pass
