"""
Cloud Workload Generator and Dataset Handler.
Generates synthetic datacenter traces featuring diurnal cycles, Poisson bursts,
multi-tenant priority distributions, and realistic resource demands.
"""
import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from src.simulator.task import Task


def generate_synthetic_workload(
    num_tasks: int = 500,
    time_horizon: int = 120,
    seed: int = 42,
    save_path: Optional[str] = None
) -> List[Task]:
    """
    Generates a reproducible heterogeneous cloud workload.
    
    Args:
        num_tasks: Total number of tasks to create.
        time_horizon: Simulation time horizon in discrete time steps (e.g., minutes).
        seed: Random seed for repeatability.
        save_path: Optional file path to persist generated workload as CSV.
        
    Returns:
        List of initialized Task objects sorted by arrival time.
    """
    rng = np.random.default_rng(seed)
    
    # Task class distributions:
    # 0: Web Microservice (50%) - low CPU/RAM, short duration, priority 2
    # 1: Batch Analytics (30%) - high CPU/RAM, long duration, priority 1
    # 2: Critical Real-time (20%) - medium CPU/RAM, strict SLA, priority 3
    task_types = [0, 1, 2]
    type_probs = [0.50, 0.30, 0.20]
    
    tasks: List[Task] = []
    task_rows: List[Dict[str, Any]] = []
    
    # Generate diurnal arrival rate curve: lambda(t) = base + amplitude * sin(2*pi*t/T)
    # Tasks are distributed across time steps according to diurnal curve
    t_vals = np.arange(time_horizon)
    diurnal_weights = 1.0 + 0.6 * np.sin(2 * np.pi * t_vals / max(1, time_horizon)) + 0.2 * rng.uniform(0, 0.5, size=len(t_vals))
    diurnal_probs = diurnal_weights / diurnal_weights.sum()
    
    # Sample arrival times
    arrival_times = rng.choice(t_vals, size=num_tasks, p=diurnal_probs)
    arrival_times.sort()
    
    for i in range(num_tasks):
        t_id = f"task_{i:04d}"
        tenant_id = f"tenant_{(i % 8) + 1}"
        arrival = int(arrival_times[i])
        cat = rng.choice(task_types, p=type_probs)
        
        if cat == 0:  # Web Microservice
            cpu = float(rng.choice([1.0, 2.0, 4.0], p=[0.5, 0.35, 0.15]))
            ram = float(rng.choice([2.0, 4.0, 8.0], p=[0.4, 0.4, 0.2]))
            dur = int(rng.integers(3, 10))
            priority = 2
            max_wait = 4
        elif cat == 1:  # Batch Analytics
            cpu = float(rng.choice([4.0, 8.0, 12.0], p=[0.4, 0.4, 0.2]))
            ram = float(rng.choice([8.0, 16.0, 32.0], p=[0.4, 0.4, 0.2]))
            dur = int(rng.integers(12, 30))
            priority = 1
            max_wait = 10
        else:  # Critical Real-time
            cpu = float(rng.choice([2.0, 4.0, 8.0], p=[0.4, 0.4, 0.2]))
            ram = float(rng.choice([4.0, 8.0, 16.0], p=[0.4, 0.4, 0.2]))
            dur = int(rng.integers(6, 18))
            priority = 3
            max_wait = 2
            
        task = Task(
            task_id=t_id,
            tenant_id=tenant_id,
            cpu_req=cpu,
            ram_req=ram,
            duration=dur,
            priority=priority,
            arrival_time=arrival,
            max_wait_tolerance=max_wait,
        )
        tasks.append(task)
        
        task_rows.append({
            "task_id": t_id,
            "tenant_id": tenant_id,
            "category": "Web" if cat == 0 else ("Batch" if cat == 1 else "Critical"),
            "cpu_req": cpu,
            "ram_req": ram,
            "duration": dur,
            "priority": priority,
            "arrival_time": arrival,
            "max_wait_tolerance": max_wait,
            "sla_deadline": task.sla_deadline,
        })
        
    if save_path:
        df = pd.DataFrame(task_rows)
        df.to_csv(save_path, index=False)
        
    return tasks
