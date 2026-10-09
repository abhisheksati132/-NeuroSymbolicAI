"""
Unit tests for Symbolic Rule Engine and constraint validation.
"""
from src.simulator.host import Host
from src.simulator.task import Task
from src.symbolic.rules import SymbolicRuleEngine


def test_rule_1_capacity_safety_bound():
    engine = SymbolicRuleEngine(max_capacity_threshold=0.85)
    host = Host("h1", "GP-4", cpu_capacity=10.0, ram_capacity=10.0)
    
    # Task fits safely within 85% (8.0 / 10.0 = 80%)
    task_ok = Task("t_ok", "tenant_1", cpu_req=8.0, ram_req=8.0, duration=5)
    admissible, score, evals = engine.evaluate_host_candidate(task_ok, host)
    assert admissible
    
    # Task would exceed 85% (9.0 / 10.0 = 90%)
    task_over = Task("t_over", "tenant_1", cpu_req=9.0, ram_req=9.0, duration=5)
    admissible_over, _, evals_over = engine.evaluate_host_candidate(task_over, host)
    assert not admissible_over
    r1_eval = next(e for e in evals_over if e.rule_id == "R1_CAPACITY_BOUND")
    assert not r1_eval.passed


def test_rule_2_sla_headroom():
    engine = SymbolicRuleEngine(high_priority_headroom_threshold=0.75)
    host = Host("h2", "GP-4", cpu_capacity=10.0, ram_capacity=10.0)
    # Put 6.0 load on host (60%)
    host.cpu_used = 6.0
    host.ram_used = 6.0
    
    # Priority 3 task adding 2.0 (total 8.0 / 10.0 = 80% > 75% headroom)
    task_p3 = Task("t_p3", "tenant_1", cpu_req=2.0, ram_req=2.0, duration=5, priority=3)
    admissible, _, evals = engine.evaluate_host_candidate(task_p3, host)
    assert not admissible
    r2_eval = next(e for e in evals if e.rule_id == "R2_SLA_HEADROOM")
    assert not r2_eval.passed


def test_rule_3_anti_affinity():
    engine = SymbolicRuleEngine()
    host = Host("h3", "GP-4", cpu_capacity=32.0, ram_capacity=64.0)
    
    # Pre-allocate existing P3 task from tenant_A
    existing_p3 = Task("t_exist", "tenant_A", cpu_req=4.0, ram_req=8.0, duration=10, priority=3)
    host.allocate(existing_p3)
    
    # Incoming second P3 task from the same tenant_A
    new_p3_same_tenant = Task("t_new", "tenant_A", cpu_req=4.0, ram_req=8.0, duration=5, priority=3)
    admissible, _, evals = engine.evaluate_host_candidate(new_p3_same_tenant, host)
    assert not admissible
    r3_eval = next(e for e in evals if e.rule_id == "R3_ANTI_AFFINITY")
    assert not r3_eval.passed
    assert "Co-location conflict" in r3_eval.reason
