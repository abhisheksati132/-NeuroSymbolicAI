"""
Generates publication-quality figures (300 DPI) for the IEEE Report.
Plots all experimental data strictly from /results raw and summary CSV files.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set clean styling
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)


def plot_architecture_diagram():
    """Generates Figure 1: System Architecture Block Diagram."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")

    # Define color scheme
    c_input = "#dbeafe"
    c_neural = "#fef3c7"
    c_symbolic = "#dcfce7"
    c_exec = "#f3e8ff"
    c_metrics = "#fee2e2"
    border = "#1e293b"

    # Draw boxes
    boxes = [
        ("Cloud Workload Stream\n(Tasks, Priorities,\nSLA Deadlines)", (0.02, 0.55), (0.18, 0.35), c_input),
        ("Historical Sliding Window\nLoad Buffer (W=12)", (0.02, 0.1), (0.18, 0.35), c_input),
        ("Neural Forecaster\n(PyTorch GRU)\nPredicts Upcoming\nCPU & RAM Demands", (0.26, 0.1), (0.20, 0.8), c_neural),
        ("Symbolic Rule Engine\n- R1: Capacity bound <=85%\n- R2: P3 SLA headroom >=25%\n- R3: Anti-affinity isolation\n- R4: Energy consolidation\n- R5: Flavor matching", (0.52, 0.1), (0.24, 0.8), c_symbolic),
        ("Heterogeneous Datacenter\n- GP-4 (16 vCPU, 64 GB)\n- CO-4 (32 vCPU, 64 GB)\n- MO-4 (16 vCPU, 128 GB)\nPower Model P(u)", (0.82, 0.45), (0.16, 0.45), c_exec),
        ("Telemetry & Metrics\n- SLA Violations\n- Rule Violations\n- Energy (kWh) & Cost\n- Decision Trace Logs", (0.82, 0.1), (0.16, 0.28), c_metrics),
    ]

    for label, (x, y), (w, h), bg in boxes:
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02",
            facecolor=bg, edgecolor=border, linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", weight="bold" if "Forecaster" in label or "Symbolic" in label else "normal")

    # Draw arrows
    arrow_props = dict(arrowstyle="->", lw=1.8, color="#0f172a")
    ax.annotate("", xy=(0.26, 0.72), xytext=(0.20, 0.72), arrowprops=arrow_props)
    ax.annotate("", xy=(0.26, 0.28), xytext=(0.20, 0.28), arrowprops=arrow_props)
    ax.annotate("", xy=(0.52, 0.5), xytext=(0.46, 0.5), arrowprops=arrow_props)
    ax.annotate("", xy=(0.82, 0.67), xytext=(0.76, 0.67), arrowprops=arrow_props)
    ax.annotate("", xy=(0.90, 0.38), xytext=(0.90, 0.45), arrowprops=arrow_props)
    ax.annotate("", xy=(0.11, 0.45), xytext=(0.82, 0.24), arrowprops=dict(arrowstyle="->", lw=1.2, color="#64748b", linestyle="dashed"))
    ax.text(0.48, 0.26, "Continuous Telemetry Feedback", color="#64748b", fontsize=8, ha="center")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig1_architecture.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")


def plot_interaction_diagram():
    """Generates Figure 2: Neural and Symbolic Component Interaction Flowchart."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis("off")

    steps = [
        ("Task Arrives: T(cpu, ram, priority, tenant)", 0.88, "#e2e8f0"),
        ("Neural Step: Predict Demand (hat_D_cpu, hat_D_ram)\nFlag Imminent Saturation if hat_D > 75%", 0.70, "#fef3c7"),
        ("Candidate Ranking & Filter:\nEvaluate Hosts against R1 (<=85%), R2 (Headroom), R3 (Anti-Affinity)", 0.50, "#dcfce7"),
        ("Admissibility Check:\nAre hard constraints satisfied?", 0.32, "#fde047"),
        ("YES: Rank by Soft Rules (R4, R5, R6) -> Place on Top Host\nEmit Auditable Decision Trace", 0.12, "#bbf7d0"),
        ("NO: Reject Candidate -> Fallback / Re-plan / Queue Task\nPreserve Zero Safety Violations", 0.12, "#fecaca"),
    ]

    # Draw nodes
    # Step 1
    rect1 = patches.FancyBboxPatch((0.2, 0.82), 0.6, 0.10, boxstyle="round,pad=0.02", facecolor="#e2e8f0", edgecolor="#334155", lw=1.5)
    ax.add_patch(rect1)
    ax.text(0.5, 0.87, "Incoming Request $T_i$ with Demand & Priority", ha="center", va="center", weight="bold")

    # Step 2
    rect2 = patches.FancyBboxPatch((0.2, 0.64), 0.6, 0.12, boxstyle="round,pad=0.02", facecolor="#fef3c7", edgecolor="#d97706", lw=1.5)
    ax.add_patch(rect2)
    ax.text(0.5, 0.70, "Neural Forecaster (GRU)\nPredicts upcoming load (D_cpu, D_ram); identifies saturation", ha="center", va="center")

    # Step 3
    rect3 = patches.FancyBboxPatch((0.2, 0.44), 0.6, 0.14, boxstyle="round,pad=0.02", facecolor="#dcfce7", edgecolor="#15803d", lw=1.5)
    ax.add_patch(rect3)
    ax.text(0.5, 0.51, "Symbolic Constraint Engine\nEvaluates Hard Rules: R1 (util <= 85%), R2 (P3 headroom), R3 (anti-affinity)", ha="center", va="center")

    # Step 4 Decision
    rect4 = patches.Polygon([[0.5, 0.38], [0.65, 0.31], [0.5, 0.24], [0.35, 0.31]], facecolor="#fed7aa", edgecolor="#ea580c", lw=1.5)
    ax.add_patch(rect4)
    ax.text(0.5, 0.31, "Hard Rules\nPassed?", ha="center", va="center", weight="bold", fontsize=8.5)

    # Step 5 Yes
    rect5 = patches.FancyBboxPatch((0.55, 0.05), 0.40, 0.14, boxstyle="round,pad=0.02", facecolor="#bbf7d0", edgecolor="#16a34a", lw=1.5)
    ax.add_patch(rect5)
    ax.text(0.75, 0.12, "PASSED: Apply Soft Rules (R4, R5, R6)\nSelect Top Host & Log Explanation Trace", ha="center", va="center", fontsize=8.5)

    # Step 6 No
    rect6 = patches.FancyBboxPatch((0.05, 0.05), 0.40, 0.14, boxstyle="round,pad=0.02", facecolor="#fecaca", edgecolor="#dc2626", lw=1.5)
    ax.add_patch(rect6)
    ax.text(0.25, 0.12, "REJECTED: Trigger Re-planning\nPower on standby or queue task\n(Prevents Server Overload)", ha="center", va="center", fontsize=8.5)

    # Connectors
    arrow = dict(arrowstyle="->", lw=1.5, color="#1e293b")
    ax.annotate("", xy=(0.5, 0.76), xytext=(0.5, 0.82), arrowprops=arrow)
    ax.annotate("", xy=(0.5, 0.58), xytext=(0.5, 0.64), arrowprops=arrow)
    ax.annotate("", xy=(0.5, 0.38), xytext=(0.5, 0.44), arrowprops=arrow)
    ax.annotate("", xy=(0.75, 0.19), xytext=(0.65, 0.31), arrowprops=arrow)
    ax.text(0.72, 0.27, "YES", color="#15803d", weight="bold")
    ax.annotate("", xy=(0.25, 0.19), xytext=(0.35, 0.31), arrowprops=arrow)
    ax.text(0.25, 0.27, "NO", color="#b91c1c", weight="bold")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig2_interaction.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")


def plot_forecast_eval():
    """Generates Figure 3: Neural Forecaster Prediction vs Actual Demand on Held-Out Test Set."""
    csv_path = os.path.join(RESULTS_DIR, "forecast_eval.csv")
    df = pd.read_csv(csv_path)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)

    # CPU Demand
    ax1.plot(df["test_step"], df["actual_cpu"], "k-", lw=1.8, label="Actual Ground Truth")
    ax1.plot(df["test_step"], df["predicted_cpu"], "b--", lw=1.8, label="GRU Forecast")
    ax1.set_ylabel("CPU Demand (vCPUs)")
    ax1.set_title("Neural Demand Forecaster: Held-Out Test Evaluation", fontweight="bold")
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.grid(True, linestyle=":", alpha=0.6)

    # RAM Demand
    ax2.plot(df["test_step"], df["actual_ram"], "k-", lw=1.8, label="Actual Ground Truth")
    ax2.plot(df["test_step"], df["predicted_ram"], "m--", lw=1.8, label="GRU Forecast")
    ax2.set_xlabel("Held-Out Test Step Index")
    ax2.set_ylabel("RAM Demand (GB)")
    ax2.legend(loc="upper right", framealpha=0.9)
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig3_forecast_vs_actual.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")


def plot_exp_a_bars():
    """Generates Figure 4: Multi-metric Benchmark Comparison for Experiment A."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "experiment_a_summary.csv"))
    algos = df["algorithm"].tolist()
    x = np.arange(len(algos))

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 7))

    # 1. Hard Rule Violations
    ax1.bar(x, df["hard_rule_violations_mean"], yerr=df["hard_rule_violations_std"], capsize=4, color="#ef4444", edgecolor="#7f1d1d")
    ax1.set_title("(a) Hard-Rule Safety Violations", fontweight="bold")
    ax1.set_ylabel("Violation Count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(algos, rotation=35, ha="right")
    ax1.grid(True, linestyle=":", alpha=0.6, axis="y")

    # 2. SLA Violation Rate (%)
    ax2.bar(x, df["sla_violation_rate_mean"], yerr=df["sla_violation_rate_std"], capsize=4, color="#f59e0b", edgecolor="#78350f")
    ax2.set_title("(b) SLA Violation Rate (%)", fontweight="bold")
    ax2.set_ylabel("Violation Rate (%)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(algos, rotation=35, ha="right")
    ax2.grid(True, linestyle=":", alpha=0.6, axis="y")

    # 3. Total Energy (kWh)
    ax3.bar(x, df["total_energy_kwh_mean"], yerr=df["total_energy_kwh_std"], capsize=4, color="#10b981", edgecolor="#064e3b")
    ax3.set_title("(c) Total Energy Consumption (kWh)", fontweight="bold")
    ax3.set_ylabel("Energy (kWh)")
    ax3.set_xticks(x)
    ax3.set_xticklabels(algos, rotation=35, ha="right")
    ax3.grid(True, linestyle=":", alpha=0.6, axis="y")

    # 4. Total Cost ($)
    ax4.bar(x, df["total_cost_usd_mean"], yerr=df["total_cost_usd_std"], capsize=4, color="#6366f1", edgecolor="#312e81")
    ax4.set_title("(d) Total Operating Cost (USD)", fontweight="bold")
    ax4.set_ylabel("Cost ($)")
    ax4.set_xticks(x)
    ax4.set_xticklabels(algos, rotation=35, ha="right")
    ax4.grid(True, linestyle=":", alpha=0.6, axis="y")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig4_exp_a_bars.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")


def plot_exp_b_scalability():
    """Generates Figure 5: Scalability Trends Across Increasing Workloads (Experiment B)."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "experiment_b_summary.csv"))
    tasks = sorted(df["workload_tasks"].unique())
    algos = df["algorithm"].unique()

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 7))

    markers = {"Round Robin": "o", "First Fit": "s", "Best Fit": "^", "Pure Symbolic": "d", "Pure Neural": "v", "Neuro-Symbolic": "D"}
    colors = {"Round Robin": "#64748b", "First Fit": "#0284c7", "Best Fit": "#8b5cf6", "Pure Symbolic": "#f59e0b", "Pure Neural": "#ef4444", "Neuro-Symbolic": "#10b981"}

    for algo in algos:
        sub = df[df["algorithm"] == algo].sort_values("workload_tasks")
        m = markers.get(algo, "o")
        c = colors.get(algo, "#000000")
        lw = 2.4 if algo == "Neuro-Symbolic" else 1.4

        # 1. SLA Violation Rate
        ax1.plot(sub["workload_tasks"], sub["sla_violation_rate_mean"], marker=m, color=c, lw=lw, label=algo)
        # 2. Hard Rule Violations
        ax2.plot(sub["workload_tasks"], sub["hard_rule_violations_mean"], marker=m, color=c, lw=lw, label=algo)
        # 3. Total Energy
        ax3.plot(sub["workload_tasks"], sub["total_energy_kwh_mean"], marker=m, color=c, lw=lw, label=algo)
        # 4. Decision Time (ms)
        ax4.plot(sub["workload_tasks"], sub["avg_decision_time_ms_mean"], marker=m, color=c, lw=lw, label=algo)

    ax1.set_title("(a) SLA Violation Rate vs. Workload", fontweight="bold")
    ax1.set_xlabel("Workload Scale (Tasks)")
    ax1.set_ylabel("SLA Violation Rate (%)")
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax2.set_title("(b) Hard-Rule Violations vs. Workload", fontweight="bold")
    ax2.set_xlabel("Workload Scale (Tasks)")
    ax2.set_ylabel("Violation Count")
    ax2.grid(True, linestyle=":", alpha=0.6)

    ax3.set_title("(c) Total Energy (kWh) vs. Workload", fontweight="bold")
    ax3.set_xlabel("Workload Scale (Tasks)")
    ax3.set_ylabel("Energy (kWh)")
    ax3.grid(True, linestyle=":", alpha=0.6)

    ax4.set_title("(d) Decision Latency vs. Workload", fontweight="bold")
    ax4.set_xlabel("Workload Scale (Tasks)")
    ax4.set_ylabel("Decision Time (ms)")
    ax4.set_yscale("log")
    ax4.grid(True, linestyle=":", alpha=0.6)

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.05))

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig5_exp_b_scalability.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")


def plot_exp_c_ablation():
    """Generates Figure 6: Ablation Study Comparison (Experiment C)."""
    df = pd.read_csv(os.path.join(RESULTS_DIR, "experiment_c_summary.csv"))
    variants = df["variant"].tolist()
    labels = ["Pure Symbolic\n(No Forecast)", "Pure Neural\n(No Rules)", "Neuro-Symbolic\n(Full)"]
    x = np.arange(len(variants))

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 3.8))

    # 1. Hard Rule Violations
    bars1 = ax1.bar(x, df["hard_rule_violations_mean"], yerr=df["hard_rule_violations_std"], capsize=4, color=["#f59e0b", "#ef4444", "#10b981"])
    ax1.set_title("(a) Hard Rule Violations", fontweight="bold")
    ax1.set_ylabel("Violation Count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=8)
    ax1.grid(True, linestyle=":", alpha=0.6, axis="y")

    # 2. Total Energy (kWh)
    bars2 = ax2.bar(x, df["total_energy_kwh_mean"], yerr=df["total_energy_kwh_std"], capsize=4, color=["#f59e0b", "#ef4444", "#10b981"])
    ax2.set_title("(b) Energy Dissipation (kWh)", fontweight="bold")
    ax2.set_ylabel("Energy (kWh)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8)
    ax2.grid(True, linestyle=":", alpha=0.6, axis="y")

    # 3. Decision Latency (ms)
    bars3 = ax3.bar(x, df["avg_decision_time_ms_mean"], yerr=df["avg_decision_time_ms_std"], capsize=4, color=["#f59e0b", "#ef4444", "#10b981"])
    ax3.set_title("(c) Decision Latency (ms)", fontweight="bold")
    ax3.set_ylabel("Latency (ms)")
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, fontsize=8)
    ax3.grid(True, linestyle=":", alpha=0.6, axis="y")

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, "fig6_exp_c_ablation.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Generated: {out_path}")


def main():
    plot_architecture_diagram()
    plot_interaction_diagram()
    plot_forecast_eval()
    plot_exp_a_bars()
    plot_exp_b_scalability()
    plot_exp_c_ablation()
    print("All 6 publication figures generated successfully at 300 DPI.")


if __name__ == "__main__":
    main()
