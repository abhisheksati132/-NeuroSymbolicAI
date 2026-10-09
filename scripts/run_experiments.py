"""
Master Experiment Runner for Cloud Resource Allocation Benchmark.
Executes Experiments A, B, and C across 5 random seeds (42, 43, 44, 45, 46).
Saves all raw run outputs and statistical summaries (mean ± std) to /results.
"""
import os
import sys
import time
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.simulator.cloud_env import CloudEnvironment
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

SEEDS = [42, 43, 44, 45, 46]


def get_allocators(forecaster):
    return {
        "Round Robin": RoundRobinAllocator(),
        "First Fit": FirstFitAllocator(),
        "Best Fit": BestFitAllocator(),
        "Pure Symbolic": PureSymbolicAllocator(),
        "Pure Neural": PureNeuralAllocator(forecaster=forecaster),
        "Neuro-Symbolic": NeuroSymbolicAllocator(forecaster=forecaster),
    }


def run_experiment_a(forecaster, results_dir):
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT A: Multi-Algorithm Benchmark (5 Seeds)")
    print("=" * 60)
    
    num_tasks = 400
    time_horizon = 120
    raw_rows = []

    for seed in SEEDS:
        print(f"--> Executing Seed {seed}...")
        tasks_base = generate_synthetic_workload(
            num_tasks=num_tasks,
            time_horizon=time_horizon,
            seed=seed,
            save_path=os.path.join(BASE_DIR, "data", f"workload_seed_{seed}.csv") if seed == 42 else None
        )
        
        allocators = get_allocators(forecaster)
        for algo_name, allocator in allocators.items():
            # Deep clone tasks for each allocator to ensure identical conditions
            tasks = [
                task.__class__(
                    task_id=task.task_id,
                    tenant_id=task.tenant_id,
                    cpu_req=task.cpu_req,
                    ram_req=task.ram_req,
                    duration=task.duration,
                    priority=task.priority,
                    arrival_time=task.arrival_time,
                    max_wait_tolerance=task.max_wait_tolerance,
                )
                for task in tasks_base
            ]
            
            env = CloudEnvironment(time_step_seconds=60.0)
            res = env.run_simulation(tasks, allocator, time_horizon=time_horizon)
            
            raw_rows.append({
                "algorithm": algo_name,
                "seed": seed,
                "num_tasks": num_tasks,
                "avg_cpu_util": res["avg_cpu_utilization"] * 100.0,
                "avg_ram_util": res["avg_ram_utilization"] * 100.0,
                "sla_violation_rate": res["sla_violation_rate"],
                "sla_violated_count": res["sla_violated_count"],
                "hard_rule_violations": res["hard_rule_violations"],
                "avg_waiting_time": res["avg_waiting_time"],
                "total_energy_kwh": res["total_energy_kwh"],
                "total_cost_usd": res["total_cost_usd"],
                "scale_events": res["scale_events"],
                "avg_decision_time_ms": res["avg_decision_time_ms"],
                "explainability_pct": res["explainability_pct"],
            })

    raw_df = pd.DataFrame(raw_rows)
    raw_path = os.path.join(results_dir, "experiment_a_raw.csv")
    raw_df.to_csv(raw_path, index=False)
    print(f"Experiment A raw data written to: {raw_path}")

    # Compute mean and standard deviation
    metric_cols = [
        "avg_cpu_util", "avg_ram_util", "sla_violation_rate", "hard_rule_violations",
        "avg_waiting_time", "total_energy_kwh", "total_cost_usd", "scale_events",
        "avg_decision_time_ms", "explainability_pct"
    ]
    
    summary_rows = []
    for algo, group in raw_df.groupby("algorithm", sort=False):
        row = {"algorithm": algo}
        for m in metric_cols:
            mean_val = group[m].mean()
            std_val = group[m].std()
            row[f"{m}_mean"] = round(mean_val, 3)
            row[f"{m}_std"] = round(std_val, 3)
        summary_rows.append(row)
        
    summary_df = pd.DataFrame(summary_rows)
    sum_path = os.path.join(results_dir, "experiment_a_summary.csv")
    summary_df.to_csv(sum_path, index=False)
    print(f"Experiment A summary written to: {sum_path}")
    print(summary_df[["algorithm", "sla_violation_rate_mean", "hard_rule_violations_mean", "total_cost_usd_mean", "total_energy_kwh_mean"]])


def run_experiment_b(forecaster, results_dir):
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT B: Scalability Analysis (100, 500, 1000, 2000 Tasks)")
    print("=" * 60)
    
    task_counts = [100, 500, 1000, 2000]
    time_horizon = 180
    raw_rows = []

    for n_tasks in task_counts:
        print(f"--> Workload scale: {n_tasks} tasks...")
        for seed in SEEDS:
            tasks_base = generate_synthetic_workload(
                num_tasks=n_tasks,
                time_horizon=time_horizon,
                seed=seed,
            )
            allocators = get_allocators(forecaster)
            for algo_name, allocator in allocators.items():
                tasks = [
                    task.__class__(
                        task_id=task.task_id,
                        tenant_id=task.tenant_id,
                        cpu_req=task.cpu_req,
                        ram_req=task.ram_req,
                        duration=task.duration,
                        priority=task.priority,
                        arrival_time=task.arrival_time,
                        max_wait_tolerance=task.max_wait_tolerance,
                    )
                    for task in tasks_base
                ]
                env = CloudEnvironment(time_step_seconds=60.0)
                res = env.run_simulation(tasks, allocator, time_horizon=time_horizon)
                
                raw_rows.append({
                    "workload_tasks": n_tasks,
                    "algorithm": algo_name,
                    "seed": seed,
                    "sla_violation_rate": res["sla_violation_rate"],
                    "hard_rule_violations": res["hard_rule_violations"],
                    "total_cost_usd": res["total_cost_usd"],
                    "total_energy_kwh": res["total_energy_kwh"],
                    "avg_decision_time_ms": res["avg_decision_time_ms"],
                    "avg_cpu_util": res["avg_cpu_utilization"] * 100.0,
                })

    raw_df = pd.DataFrame(raw_rows)
    raw_path = os.path.join(results_dir, "experiment_b_raw.csv")
    raw_df.to_csv(raw_path, index=False)
    print(f"Experiment B raw data written to: {raw_path}")

    # Summarize mean and std grouped by (workload_tasks, algorithm)
    summary_rows = []
    for (n_tasks, algo), group in raw_df.groupby(["workload_tasks", "algorithm"], sort=False):
        summary_rows.append({
            "workload_tasks": n_tasks,
            "algorithm": algo,
            "sla_violation_rate_mean": round(group["sla_violation_rate"].mean(), 3),
            "sla_violation_rate_std": round(group["sla_violation_rate"].std(), 3),
            "hard_rule_violations_mean": round(group["hard_rule_violations"].mean(), 3),
            "hard_rule_violations_std": round(group["hard_rule_violations"].std(), 3),
            "total_cost_usd_mean": round(group["total_cost_usd"].mean(), 3),
            "total_cost_usd_std": round(group["total_cost_usd"].std(), 3),
            "total_energy_kwh_mean": round(group["total_energy_kwh"].mean(), 3),
            "total_energy_kwh_std": round(group["total_energy_kwh"].std(), 3),
            "avg_decision_time_ms_mean": round(group["avg_decision_time_ms"].mean(), 4),
            "avg_decision_time_ms_std": round(group["avg_decision_time_ms"].std(), 4),
        })
    summary_df = pd.DataFrame(summary_rows)
    sum_path = os.path.join(results_dir, "experiment_b_summary.csv")
    summary_df.to_csv(sum_path, index=False)
    print(f"Experiment B summary written to: {sum_path}")


def run_experiment_c(forecaster, results_dir):
    print("\n" + "=" * 60)
    print("RUNNING EXPERIMENT C: Ablation Study (No Forecast, No Rules, Full)")
    print("=" * 60)
    
    num_tasks = 600
    time_horizon = 140
    raw_rows = []

    ablation_allocators = {
        "Without Forecast (Pure Symbolic)": PureSymbolicAllocator(),
        "Without Rules (Pure Neural)": PureNeuralAllocator(forecaster=forecaster),
        "Full Neuro-Symbolic": NeuroSymbolicAllocator(forecaster=forecaster),
    }

    for seed in SEEDS:
        tasks_base = generate_synthetic_workload(
            num_tasks=num_tasks,
            time_horizon=time_horizon,
            seed=seed,
        )
        for variant_name, allocator in ablation_allocators.items():
            tasks = [
                task.__class__(
                    task_id=task.task_id,
                    tenant_id=task.tenant_id,
                    cpu_req=task.cpu_req,
                    ram_req=task.ram_req,
                    duration=task.duration,
                    priority=task.priority,
                    arrival_time=task.arrival_time,
                    max_wait_tolerance=task.max_wait_tolerance,
                )
                for task in tasks_base
            ]
            env = CloudEnvironment(time_step_seconds=60.0)
            res = env.run_simulation(tasks, allocator, time_horizon=time_horizon)

            raw_rows.append({
                "variant": variant_name,
                "seed": seed,
                "sla_violation_rate": res["sla_violation_rate"],
                "hard_rule_violations": res["hard_rule_violations"],
                "avg_cpu_util": res["avg_cpu_utilization"] * 100.0,
                "avg_ram_util": res["avg_ram_utilization"] * 100.0,
                "total_cost_usd": res["total_cost_usd"],
                "total_energy_kwh": res["total_energy_kwh"],
                "avg_decision_time_ms": res["avg_decision_time_ms"],
                "explainability_pct": res["explainability_pct"],
            })

    raw_df = pd.DataFrame(raw_rows)
    raw_path = os.path.join(results_dir, "experiment_c_raw.csv")
    raw_df.to_csv(raw_path, index=False)
    print(f"Experiment C raw data written to: {raw_path}")

    summary_rows = []
    for var, group in raw_df.groupby("variant", sort=False):
        summary_rows.append({
            "variant": var,
            "sla_violation_rate_mean": round(group["sla_violation_rate"].mean(), 3),
            "sla_violation_rate_std": round(group["sla_violation_rate"].std(), 3),
            "hard_rule_violations_mean": round(group["hard_rule_violations"].mean(), 3),
            "hard_rule_violations_std": round(group["hard_rule_violations"].std(), 3),
            "avg_cpu_util_mean": round(group["avg_cpu_util"].mean(), 3),
            "avg_cpu_util_std": round(group["avg_cpu_util"].std(), 3),
            "total_cost_usd_mean": round(group["total_cost_usd"].mean(), 3),
            "total_cost_usd_std": round(group["total_cost_usd"].std(), 3),
            "total_energy_kwh_mean": round(group["total_energy_kwh"].mean(), 3),
            "total_energy_kwh_std": round(group["total_energy_kwh"].std(), 3),
            "avg_decision_time_ms_mean": round(group["avg_decision_time_ms"].mean(), 4),
            "avg_decision_time_ms_std": round(group["avg_decision_time_ms"].std(), 4),
            "explainability_pct_mean": round(group["explainability_pct"].mean(), 1),
            "explainability_pct_std": round(group["explainability_pct"].std(), 1),
        })
    summary_df = pd.DataFrame(summary_rows)
    sum_path = os.path.join(results_dir, "experiment_c_summary.csv")
    summary_df.to_csv(sum_path, index=False)
    print(f"Experiment C summary written to: {sum_path}")
    print(summary_df[["variant", "sla_violation_rate_mean", "hard_rule_violations_mean", "total_cost_usd_mean", "explainability_pct_mean"]])


def main():
    results_dir = os.path.join(BASE_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    forecaster = DemandForecaster()
    model_path = os.path.join(results_dir, "demand_forecaster.pt")
    if os.path.exists(model_path):
        forecaster.load_model(model_path)
        print(f"Loaded trained forecaster from: {model_path}")
    else:
        print("Warning: demand_forecaster.pt not found! Train it first.")

    start_total = time.time()
    run_experiment_a(forecaster, results_dir)
    run_experiment_b(forecaster, results_dir)
    run_experiment_c(forecaster, results_dir)
    total_sec = time.time() - start_total
    print(f"\nALL EXPERIMENTS COMPLETED SUCCESSFULLY in {total_sec:.2f} seconds.")


if __name__ == "__main__":
    main()
