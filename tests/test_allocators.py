"""
Unit tests for Allocators and comparative behaviors.
"""
from src.simulator.cloud_env import CloudEnvironment, create_default_heterogeneous_cluster
from src.simulator.task import Task
from src.neural.forecaster import DemandForecaster
from src.allocator.baselines import (
    RoundRobinAllocator,
    FirstFitAllocator,
    BestFitAllocator,
    PureSymbolicAllocator,
)
from src.allocator.neuro_symbolic import NeuroSymbolicAllocator


def test_allocator_executions():
    hosts = create_default_heterogeneous_cluster(num_hosts=6)
    env = CloudEnvironment(hosts=hosts)
    
    task = Task("t_alloc", "tenant_1", cpu_req=4.0, ram_req=8.0, duration=10, priority=2)
    
    rr = RoundRobinAllocator()
    res_rr = rr.allocate(task, env.hosts, env=env)
    assert res_rr["target_host_id"] is not None
    
    ff = FirstFitAllocator()
    res_ff = ff.allocate(task, env.hosts, env=env)
    assert res_ff["target_host_id"] is not None

    bf = BestFitAllocator()
    res_bf = bf.allocate(task, env.hosts, env=env)
    assert res_bf["target_host_id"] is not None

    sym = PureSymbolicAllocator()
    res_sym = sym.allocate(task, env.hosts, env=env)
    assert res_sym["target_host_id"] is not None
    assert "Pure Symbolic accepted" in res_sym["trace"]

    forecaster = DemandForecaster()
    ns = NeuroSymbolicAllocator(forecaster=forecaster)
    res_ns = ns.allocate(task, env.hosts, env=env)
    assert res_ns["target_host_id"] is not None
    assert not res_ns["hard_rule_violated"]
    assert "Trace:" in res_ns["trace"]
