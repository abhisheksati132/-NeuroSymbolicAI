"""
Trains and evaluates the GRU Neural Demand Forecaster on datacenter workload timeseries.
Saves model weights, evaluation test timeseries, and error metrics (MAE, RMSE).
"""
import os
import sys
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.simulator.workload import generate_synthetic_workload
from src.neural.forecaster import DemandForecaster


def generate_training_series(steps: int = 300, seed: int = 101) -> np.ndarray:
    """
    Simulates demand arrivals across 300 time steps to form a continuous
    CPU and RAM aggregate timeseries for training and testing.
    """
    tasks = generate_synthetic_workload(num_tasks=1200, time_horizon=steps, seed=seed)
    
    # Track demand at each step
    cpu_demands = np.zeros(steps)
    ram_demands = np.zeros(steps)
    
    for t in tasks:
        end_step = min(steps, t.arrival_time + t.duration)
        cpu_demands[t.arrival_time : end_step] += t.cpu_req
        ram_demands[t.arrival_time : end_step] += t.ram_req

    # Stack into (T, 2)
    series = np.column_stack([cpu_demands, ram_demands])
    return series


def main():
    results_dir = os.path.join(BASE_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    model_save_path = os.path.join(results_dir, "demand_forecaster.pt")
    eval_csv_path = os.path.join(results_dir, "forecast_eval.csv")
    metrics_json_path = os.path.join(results_dir, "forecast_metrics.json")

    print("[1/3] Generating training timeseries trace (300 steps, seed 101)...")
    series = generate_training_series(steps=300, seed=101)

    print("[2/3] Initializing GRU Forecaster (window=12, hidden_dim=32) and training...")
    forecaster = DemandForecaster(window_size=12, hidden_dim=32)
    metrics = forecaster.train_model(
        time_series=series,
        epochs=60,
        lr=0.005,
        save_path=model_save_path,
        results_csv_path=eval_csv_path,
    )

    print(f"[3/3] Training and held-out evaluation complete:")
    print(f"      CPU Demand -> MAE: {metrics['mae_cpu']} cores | RMSE: {metrics['rmse_cpu']} cores")
    print(f"      RAM Demand -> MAE: {metrics['mae_ram']} GB    | RMSE: {metrics['rmse_ram']} GB")
    print(f"      Test samples: {metrics['test_samples']}")

    with open(metrics_json_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Outputs saved:\n - {model_save_path}\n - {eval_csv_path}\n - {metrics_json_path}")


if __name__ == "__main__":
    main()
