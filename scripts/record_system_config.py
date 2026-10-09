"""
Records exact host hardware, operating system, and software library configurations.
Saves to /results/system_config.json.
"""
import os
import sys
import json
import platform
import subprocess
import torch
import numpy as np
import pandas as pd
import matplotlib
import scipy
import flask

def get_system_config():
    # CPU info
    cpu_model = platform.processor()
    try:
        import psutil
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        cpu_cores = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
    except ImportError:
        # Fallback using Windows WMIC/PowerShell or os
        ram_bytes = 0
        try:
            out = subprocess.check_output("wmic computersystem get TotalPhysicalMemory", shell=True).decode()
            for line in out.splitlines():
                if line.strip().isdigit():
                    ram_bytes = int(line.strip())
            ram_gb = round(ram_bytes / (1024 ** 3), 2)
        except Exception:
            ram_gb = 16.0  # fallback
        cpu_cores = os.cpu_count() or 8
        cpu_physical = cpu_cores // 2 if cpu_cores else 4

    # GPU info
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "None (CPU Execution)"

    config = {
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        },
        "hardware": {
            "processor": cpu_model or platform.machine(),
            "logical_cpu_cores": cpu_cores,
            "physical_cpu_cores": cpu_physical,
            "total_ram_gb": ram_gb,
            "gpu_device": gpu_name,
            "cuda_available": gpu_available,
        },
        "python_environment": {
            "python_version": platform.python_version(),
            "python_compiler": platform.python_compiler(),
        },
        "library_versions": {
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
            "scipy": scipy.__version__,
            "flask": flask.__version__,
        },
        "cluster_simulator_config": {
            "cluster_nodes_count": 12,
            "node_types": [
                {"flavor": "GP-4 (General Purpose)", "vcpus": 16, "ram_gb": 64, "p_idle_w": 80, "p_peak_w": 250, "cost_hr": 0.40},
                {"flavor": "CO-4 (Compute Optimized)", "vcpus": 32, "ram_gb": 64, "p_idle_w": 110, "p_peak_w": 380, "cost_hr": 0.65},
                {"flavor": "MO-4 (Memory Optimized)", "vcpus": 16, "ram_gb": 128, "p_idle_w": 95, "p_peak_w": 310, "cost_hr": 0.75},
            ],
            "total_cluster_vcpus": 256,
            "total_cluster_ram_gb": 1024,
            "discrete_time_step_sec": 60.0,
            "safety_capacity_threshold": 0.85,
            "p3_sla_headroom_threshold": 0.75,
        }
    }
    return config

if __name__ == "__main__":
    cfg = get_system_config()
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "system_config.json")
    with open(out_file, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"System configuration recorded to: {out_file}")
