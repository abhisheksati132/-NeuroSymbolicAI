"""
Interactive Flask Dashboard for Neuro-Symbolic Cloud Resource Allocation.
Provides live interactive simulations, KPI telemetry, rule trace audits,
and multi-algorithm comparisons.
"""
import os
import sys
from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.simulator.cloud_env import CloudEnvironment, create_default_heterogeneous_cluster
from src.simulator.workload import generate_synthetic_workload
from src.neural.forecaster import DemandForecaster
from src.allocator.baselines import (
    RoundRobinAllocator,
    FirstFitAllocator,
    BestFitAllocator,
    PureSymbolicAllocator,
    PureNeuralAllocator,
)
from src.allocator.neuro_symbolic import NeuroSymbolicAllocator

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask(__name__, template_folder=template_dir)

# Initialize demand forecaster
forecaster = DemandForecaster()
model_npz = os.path.join(BASE_DIR, "results", "demand_forecaster_weights.npz")
model_pt = os.path.join(BASE_DIR, "results", "demand_forecaster.pt")
if os.path.exists(model_npz):
    try:
        forecaster.load_model(model_npz)
    except Exception as e:
        print(f"Warning loading NPZ weights: {e}")
elif os.path.exists(model_pt):
    try:
        forecaster.load_model(model_pt)
    except Exception as e:
        print(f"Warning loading PT model: {e}")


def get_allocator(name: str):
    name_clean = name.strip().lower()
    if "round" in name_clean:
        return RoundRobinAllocator()
    elif "first" in name_clean:
        return FirstFitAllocator()
    elif "best" in name_clean:
        return BestFitAllocator()
    elif "pure symbolic" in name_clean or "rule" in name_clean:
        return PureSymbolicAllocator()
    elif "pure neural" in name_clean:
        return PureNeuralAllocator(forecaster=forecaster)
    elif "neuro-symbolic" in name_clean or "neuro" in name_clean:
        return NeuroSymbolicAllocator(forecaster=forecaster)
    else:
        return NeuroSymbolicAllocator(forecaster=forecaster)


@app.route("/", methods=["GET", "POST"])
@app.route("/api", methods=["GET", "POST"])
@app.route("/api/index", methods=["GET", "POST"])
@app.route("/api/index.py", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return run_simulation_api()
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
@app.route("/run", methods=["POST"])
def run_simulation_api():
    data = request.json or {}
    algo_name = data.get("algorithm", "Neuro-Symbolic (Proposed)")
    num_tasks = int(data.get("num_tasks", 300))
    seed = int(data.get("seed", 42))
    time_horizon = int(data.get("time_horizon", 100))

    # Generate workload
    tasks = generate_synthetic_workload(
        num_tasks=num_tasks,
        time_horizon=time_horizon,
        seed=seed,
    )

    env = CloudEnvironment(time_step_seconds=60.0)
    allocator = get_allocator(algo_name)

    # Run simulation
    # To capture individual task traces for UI table
    task_traces = []
    
    # Custom simulation loop wrapper to collect audit rows
    tasks_by_arrival = {}
    for t in tasks:
        tasks_by_arrival.setdefault(t.arrival_time, []).append(t)

    import time
    env.reset()
    decision_latencies = []
    total_allocations = 0
    traces_recorded = 0
    hard_violations = 0

    for step in range(time_horizon):
        env.current_step = step
        # Step active tasks
        still_active = []
        for task in env.active_tasks:
            if task.step(step):
                if task.host_id:
                    host = next((h for h in env.hosts if h.host_id == task.host_id), None)
                    if host:
                        host.release(task.task_id)
                env.completed_tasks.append(task)
            else:
                still_active.append(task)
        env.active_tasks = still_active

        # Add arrivals
        new_tasks = tasks_by_arrival.get(step, [])
        env.pending_queue.extend(new_tasks)
        for pt in env.pending_queue:
            pt.step(step)

        # Place pending
        unplaced = []
        while env.pending_queue:
            task_to_place = env.pending_queue.pop(0)
            t_start = time.perf_counter()
            dec = allocator.allocate(task_to_place, env.hosts, env=env)
            lat_ms = (time.perf_counter() - t_start) * 1000.0
            decision_latencies.append(lat_ms)
            total_allocations += 1

            target_id = dec.get("target_host_id")
            trace = dec.get("trace", "")
            violated = dec.get("hard_rule_violated", False)
            if trace:
                traces_recorded += 1
            if violated:
                hard_violations += 1

            if len(task_traces) < 60:
                task_traces.append({
                    "task_id": task_to_place.task_id,
                    "tenant": task_to_place.tenant_id,
                    "priority": task_to_place.priority,
                    "cpu_req": task_to_place.cpu_req,
                    "ram_req": task_to_place.ram_req,
                    "target_host": target_id if target_id else "REJECTED/QUEUED",
                    "hard_violation": violated,
                    "trace": trace,
                })

            if target_id:
                host = next((h for h in env.hosts if h.host_id == target_id), None)
                if host and host.allocate(task_to_place):
                    task_to_place.allocated = True
                    task_to_place.start_time = step
                    env.active_tasks.append(task_to_place)
                else:
                    unplaced.append(task_to_place)
            else:
                unplaced.append(task_to_place)

        env.pending_queue = unplaced
        curr_active_hosts = {h.host_id for h in env.hosts if h.is_active}
        newly_act = curr_active_hosts - env.last_active_host_ids
        env.scale_events += len(newly_act)
        env.last_active_host_ids = curr_active_hosts

        for h in env.hosts:
            h.step(env.time_step_seconds)

        env.step_history.append({
            "step": step,
            "cpu_util": round(env.cluster_cpu_utilization * 100, 2),
            "ram_util": round(env.cluster_ram_utilization * 100, 2),
            "power_watts": round(env.cluster_power_watts, 1),
            "active_hosts": len(curr_active_hosts),
            "active_tasks": len(env.active_tasks),
        })

    for t in env.active_tasks:
        env.completed_tasks.append(t)
    for t in env.pending_queue:
        t.sla_violated = True
        env.completed_tasks.append(t)

    all_done = env.completed_tasks
    sla_viols = sum(1 for t in all_done if t.sla_violated)
    sla_rate = (sla_viols / len(all_done) * 100.0) if all_done else 0.0
    energy_kwh = sum(h.total_energy_joules for h in env.hosts) / 3.6e6
    cost_usd = sum(h.cost_per_hour * (h.total_active_seconds / 3600.0) for h in env.hosts)
    avg_lat = float(np.mean(decision_latencies)) if decision_latencies else 0.0
    explain_pct = (traces_recorded / total_allocations * 100.0) if total_allocations > 0 else 0.0
    avg_cpu = float(np.mean([s["cpu_util"] for s in env.step_history]))
    avg_ram = float(np.mean([s["ram_util"] for s in env.step_history]))

    return jsonify({
        "metrics": {
            "avg_cpu_util": round(avg_cpu, 2),
            "avg_ram_util": round(avg_ram, 2),
            "sla_violation_rate": round(sla_rate, 2),
            "hard_rule_violations": hard_violations,
            "energy_kwh": round(energy_kwh, 4),
            "cost_usd": round(cost_usd, 3),
            "scale_events": env.scale_events,
            "decision_latency_ms": round(avg_lat, 3),
            "explainability_pct": round(explain_pct, 1),
        },
        "step_history": env.step_history,
        "task_traces": task_traces,
    })


@app.errorhandler(404)
def handle_404(e):
    if request.method == "GET":
        return render_template("index.html")
    return jsonify({"error": "Resource not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
