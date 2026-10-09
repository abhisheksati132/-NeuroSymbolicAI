"""
Unit tests for Simulator components: Host, Task, and Workload.
"""
import pytest
from src.simulator.host import Host
from src.simulator.task import Task
from src.simulator.workload import generate_synthetic_workload
from src.simulator.cloud_env import CloudEnvironment, create_default_heterogeneous_cluster


def test_host_allocation_and_release():
    host = Host(
        host_id="h-test",
        host_type="GP-4",
        cpu_capacity=16.0,
        ram_capacity=64.0,
        p_idle=80.0,
        p_peak=250.0,
    )
    assert host.cpu_used == 0.0
    assert host.ram_used == 0.0
    assert not host.is_active
    assert host.current_power_watts == host.p_standby

    task = Task(task_id="t1", tenant_id="tenant_1", cpu_req=4.0, ram_req=16.0, duration=5)
    success = host.allocate(task)
    assert success
    assert host.is_active
    assert host.cpu_used == 4.0
    assert host.ram_used == 16.0
    assert host.cpu_utilization == 4.0 / 16.0
    assert host.ram_utilization == 16.0 / 64.0

    # Power should now be active
    expected_power = 80.0 + (250.0 - 80.0) * max(4.0 / 16.0, 16.0 / 64.0)
    assert abs(host.current_power_watts - expected_power) < 1e-4

    released = host.release(task.task_id)
    assert released == task
    assert host.cpu_used == 0.0
    assert host.ram_used == 0.0


def test_task_sla_and_lifecycle():
    task = Task(
        task_id="t2",
        tenant_id="tenant_2",
        cpu_req=2.0,
        ram_req=4.0,
        duration=3,
        priority=3,
        arrival_time=0,
        max_wait_tolerance=2,
    )
    assert task.sla_deadline == 0 + 2 + 3
    assert not task.sla_violated

    # Simulate waiting beyond tolerance without allocation
    task.step(0)
    task.step(1)
    task.step(2)
    assert task.waiting_time == 3
    assert task.sla_violated


def test_workload_generator_reproducibility():
    w1 = generate_synthetic_workload(num_tasks=50, time_horizon=60, seed=123)
    w2 = generate_synthetic_workload(num_tasks=50, time_horizon=60, seed=123)
    assert len(w1) == len(w2) == 50
    for t1, t2 in zip(w1, w2):
        assert t1.cpu_req == t2.cpu_req
        assert t1.ram_req == t2.ram_req
        assert t1.arrival_time == t2.arrival_time
