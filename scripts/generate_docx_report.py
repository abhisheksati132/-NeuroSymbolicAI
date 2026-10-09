"""
Generates a DOCX version of the IEEE Case Study Report.
Uses python-docx to generate /report/report.docx with full formatting,
tables, figures, and authentic experimental numbers.
"""
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(BASE_DIR, "report")
DOCX_PATH = os.path.join(REPORT_DIR, "report.docx")

def build_docx():
    doc = docx.Document()

    # Page setup: Letter, 0.75 in margins
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # ----------------------------------------------------
    # COVER PAGE
    # ----------------------------------------------------
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_inst = p_inst.add_run("VELLORE INSTITUTE OF TECHNOLOGY\nSchool of Computer Science and Engineering (SCOPE)")
    run_inst.font.size = Pt(16)
    run_inst.font.bold = True
    run_inst.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    p_course = doc.add_paragraph()
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_course = p_course.add_run("COURSE CASE STUDY REPORT\nBCSE355L -- Cloud Architecture Design\nFaculty In-Charge: Prof. Padmavathy T")
    run_course.font.size = Pt(13)
    run_course.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(20)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("Cloud Resource Allocation using Neuro-Symbolic AI\n")
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(2, 132, 199)
    run_sub = p_title.add_run("A Predictive, Constraint-Guaranteed, and Auditable Orchestration Framework for Heterogeneous Cloud Datacenters")
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True

    doc.add_paragraph().paragraph_format.space_after = Pt(30)

    # Team Table
    p_team_hdr = doc.add_paragraph()
    p_team_hdr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_th = p_team_hdr.add_run("PROJECT TEAM DETAILS")
    r_th.font.bold = True
    r_th.font.size = Pt(12)

    table_team = doc.add_table(rows=4, cols=3)
    table_team.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["S. No.", "Student Name", "Registration Number"]
    for i, h in enumerate(headers):
        cell = table_team.cell(0, i)
        cell.text = h
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    team_data = [
        ("1", "Deepanshu Agarwal", "24BCI0142"),
        ("2", "Sanjay Giridhar K", "24BCE0581"),
        ("3", "Abhishek Sati", "24BDS0199"),
    ]
    for row_idx, data in enumerate(team_data, start=1):
        for col_idx, text in enumerate(data):
            cell = table_team.cell(row_idx, col_idx)
            cell.text = text
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph().paragraph_format.space_after = Pt(40)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.add_run("Academic Session & Class Slot: [TO BE FILLED]\nDate of Submission: October 2026").font.size = Pt(11)

    doc.add_page_break()

    # ----------------------------------------------------
    # IEEE REPORT BODY
    # ----------------------------------------------------
    # Paper Title
    p_body_title = doc.add_heading(level=1)
    p_body_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_bt = p_body_title.add_run("Cloud Resource Allocation using Neuro-Symbolic AI: A Predictive, Constraint-Guaranteed, and Auditable Orchestration Framework")
    r_bt.font.size = Pt(16)
    r_bt.font.bold = True

    # Authors
    p_authors = doc.add_paragraph()
    p_authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_authors.add_run("Deepanshu Agarwal (24BCI0142)  |  Sanjay Giridhar K (24BCE0581)  |  Abhishek Sati (24BDS0199)\n").font.bold = True
    p_authors.add_run("School of Computer Science and Engineering (SCOPE), Vellore Institute of Technology, India")

    # Abstract
    p_abs = doc.add_paragraph()
    r_absh = p_abs.add_run("Abstract—")
    r_absh.font.bold = True
    p_abs.add_run("Modern multi-tenant cloud datacenters face conflicting operational objectives: maximizing server consolidation to minimize power dissipation while upholding stringent Service Level Agreements (SLAs) and preventing physical host saturation. Traditional heuristic schedulers such as First Fit and Best Fit operate reactively, packing workloads until servers breach safe thermal and hypervisor capacity thresholds. Conversely, black-box deep reinforcement learning or neural allocators lack hard safety guarantees and fail to provide explainable operational reasoning required by mission-critical cloud operators. This paper presents a cohesive Neuro-Symbolic Cloud Resource Allocator that bridges data-driven statistical demand forecasting with explicit, deterministic symbolic constraint reasoning. The neural component implements a Gated Recurrent Unit (GRU) sequence forecaster predicting cluster-wide CPU and memory demands over sliding observation windows. The symbolic component enforces first-order operational constraints including an 85% host safety ceiling, priority-specific SLA headroom, multi-tenant failure-domain anti-affinity, and proactive standby activation. In empirical benchmarks conducted across five distinct random seeds on heterogeneous datacenter topologies, the proposed neuro-symbolic system completely eliminated hard-rule safety violations (0.0 ± 0.0 violations compared to 320.8 ± 10.7 for Best Fit and 207.2 ± 34.3 for Pure Neural), achieved the lowest total datacenter energy consumption (5.776 ± 0.150 kWh), and logged auditable rule execution traces for 100% of allocation decisions with sub-millisecond latency (0.886 ± 0.029 ms).")

    p_kw = doc.add_paragraph()
    p_kw.add_run("Index Terms—").font.bold = True
    p_kw.add_run("Cloud Resource Allocation, Neuro-Symbolic AI, Gated Recurrent Units, Symbolic Constraint Reasoning, SLA Enforcement, Energy Consolidation.")

    # Sections
    sections_text = [
        ("I. Introduction", [
            "Contemporary hyper-scale and enterprise cloud infrastructures host diverse, heterogeneous workloads ranging from bursty user-facing microservices to compute-heavy batch analytics. Operating these multi-tenant environments requires cloud management platforms to continuously solve high-dimensional online bin-packing problems. The primary objectives are inherently multi-objective: minimizing operational expenditures and server energy consumption through consolidation while strictly honoring Service Level Agreements (SLAs) and isolating failure domains.",
            "In current production environments, scheduling decisions are predominantly governed by classic online heuristics, such as Round Robin, First Fit, and Best Fit Decreasing. While computationally lightweight, these heuristic policies are purely reactive and state-agnostic. They evaluate only the instantaneous resource availability of physical hosts without anticipating forthcoming traffic spikes. Under diurnal surges or sudden bursts, reactive packing drives physical servers beyond safe operational thresholds (typically 80%–85% CPU and memory utilization), triggering severe hypervisor thrashing, memory swapping, and tail-latency SLA penalties.",
            "To counteract the myopia of static heuristics, recent literature has explored statistical machine learning and deep reinforcement learning (DRL) allocators. Although neural networks excel at capturing non-linear temporal workload patterns, pure neural allocators suffer from critical deficiencies: absence of safety guarantees (causing out-of-distribution capacity breaches) and opacity/lack of explainability (preventing SRE audits).",
            "This study investigates Neuro-Symbolic Artificial Intelligence applied to cloud resource orchestration. By coupling statistical sequence forecasting with an explicit declarative rule and constraint verification engine, we create a hybrid architecture where neural predictions guide proactive capacity readiness while symbolic rules strictly validate, filter, and explain every placement decision."
        ]),
        ("II. Related Work", [
            "Beloglazov and Buyya formulated foundational heuristics for energy-efficient dynamic virtual machine (VM) consolidation in cloud datacenters using modified Best Fit Decreasing algorithms. While effective, their threshold heuristics remained reactive.",
            "Analysis of Google datacenter traces by Reiss et al. demonstrated that production workloads exhibit severe dynamicity and burstiness. Shen et al. developed CloudScale for predictive elasticity, and Farahnakian et al. applied sliding-window regression for host load forecasting.",
            "In server power modeling, Fan, Weber, and Barroso established that datacenter server power scales linearly with active CPU and memory load between idle baseline power and peak capacity. Our simulation directly implements this validated linear-utilization curve.",
            "Garcez et al. formalized neuro-symbolic computing paradigms, pairing statistical representations with symbolic knowledge. Our study operationalizes this paradigm for cloud resource allocation."
        ]),
        ("III. System Configuration", [
            "All experiments were conducted on an AMD64 Family 25 processor (8 physical cores, 16 logical threads, 16 GB RAM) running Windows 11 Enterprise and Python 3.14.6 with PyTorch 2.13.0, recorded automatically to /results/system_config.json.",
            "The cluster consists of 12 heterogeneous nodes partitioned across General Purpose (GP-4, 16 vCPU, 64 GB RAM, 80W idle, 250W peak, $0.40/hr), Compute Optimized (CO-4, 32 vCPU, 64 GB RAM, 110W idle, 380W peak, $0.65/hr), and Memory Optimized (MO-4, 16 vCPU, 128 GB RAM, 95W idle, 310W peak, $0.75/hr) server types, providing 256 vCPUs and 1024 GB RAM.",
            "The synthetic workload models a sinusoidal diurnal cycle with stochastic Poisson bursts, multi-tier task categories (Web 50%, Batch 30%, Critical 20%), explicit priorities, and 10 tenant domains."
        ]),
        ("IV. System Architecture & Methodology", [
            "The full pipeline integrates workload arrival buffering, a PyTorch GRU demand forecaster (2 layers, hidden dimension 32, predicting upcoming CPU/RAM load), a Symbolic Constraint Engine enforcing 6 explicit rules (R1: Capacity Bound <=85%, R2: SLA Headroom >=25% for P3, R3: Anti-affinity tenant isolation, R4: Energy packing bonus, R5: Flavor matching, R6: Proactive saturation headroom reservation), and telemetry feedback.",
            "The allocator guarantees 100% explainability: every decision records candidate host evaluations, passed/failed constraints, and the rationale for the final selection."
        ]),
        ("V. Experimental Results & Inferences", [
            "Neural Forecaster Accuracy: Evaluated on held-out test splits, the GRU forecaster achieved CPU Demand MAE = 15.8565 cores (RMSE = 19.4177 cores) and RAM Demand MAE = 46.5265 GB (RMSE = 59.0780 GB).",
            "Experiment A Benchmark (400 tasks, 5 seeds): Best Fit produced 320.8 ± 10.7 hard-rule violations, First Fit produced 306.6 ± 22.5, Round Robin produced 237.8 ± 34.8, and Pure Neural produced 207.2 ± 34.3. Neuro-Symbolic achieved exactly 0.0 ± 0.0 hard violations, lowest energy dissipation (5.776 ± 0.150 kWh vs 6.092 kWh for Round Robin), and sub-millisecond decision latency (0.886 ± 0.029 ms).",
            "Experiment B Scalability (100 to 2000 tasks): Under 1000 tasks, reactive heuristics suffered severe collapse (First Fit: 85.18% SLA violations, 752.8 hard violations), whereas Neuro-Symbolic achieved 57.24% SLA violations, 0.0 hard violations, and 14.0% lower energy (9.496 kWh vs 11.050 kWh).",
            "Experiment C Ablation (600 tasks): Disabling symbolic rules (Pure Neural) resulted in 474.0 ± 24.3 hard violations and excessive CPU overutilization (90.73%), conclusively demonstrating that statistical models require symbolic safety bounds."
        ]),
        ("VI. Discussion & Limitations", [
            "Discrete simulation abstracts physical hypervisor virtualization overheads (cache interference, hypervisor lock contention).",
            "The synthetic trace models diurnal patterns but does not capture multi-day non-stationary production shifts.",
            "Expanding the symbolic rule base to cover regulatory data sovereignty and NUMA topology remains future work."
        ]),
        ("VII. Conclusion", [
            "The proposed Neuro-Symbolic Cloud Allocator provides proactive operational readiness while guaranteeing hard mathematical safety bounds, zero rule breaches, lowest energy consumption, and 100% auditability."
        ])
    ]

    for title, paras in sections_text:
        h = doc.add_heading(level=2)
        h.add_run(title).font.bold = True
        for p_txt in paras:
            p = doc.add_paragraph()
            p.add_run(p_txt)

    # Add images if available
    doc.add_heading("System Architecture & Figures", level=2)
    figs = [
        ("figures/fig1_architecture.png", "Figure 1: Full System Architecture Block Diagram"),
        ("figures/fig2_interaction.png", "Figure 2: Neural and Symbolic Component Interaction Flowchart"),
        ("figures/fig3_forecast_vs_actual.png", "Figure 3: Neural Forecaster Prediction vs Actual Ground Truth"),
        ("figures/fig4_exp_a_bars.png", "Figure 4: Experiment A Multi-Algorithm Benchmark Comparison"),
        ("figures/fig5_exp_b_scalability.png", "Figure 5: Experiment B Scalability Trends"),
        ("figures/fig6_exp_c_ablation.png", "Figure 6: Experiment C Architectural Ablation Study"),
        ("screenshots/simulation_results.png", "Figure 7: Live Simulation Results View in Demo Dashboard"),
        ("screenshots/rule_trace_explanation.png", "Figure 8: Auditable Symbolic Rule Trace Decision Log Table"),
    ]

    for f_rel, caption in figs:
        f_abs = os.path.join(BASE_DIR, f_rel)
        if os.path.exists(f_abs):
            doc.add_paragraph().paragraph_format.space_before = Pt(10)
            doc.add_picture(f_abs, width=Inches(6.0))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.add_run(caption).font.italic = True

    # References
    doc.add_heading("References", level=2)
    refs = [
        "[1] X. Fan, W.-D. Weber, and L. A. Barroso, 'Power provisioning for a warehouse-sized computer,' in Proc. 34th Annu. Int. Symp. Comput. Archit. (ISCA), 2007, pp. 13-23.",
        "[2] A. Beloglazov and R. Buyya, 'Optimal online deterministic algorithms and adaptive heuristics for energy and performance efficient dynamic consolidation of virtual machines in Cloud data centers,' Concurrency and Computation: Practice and Experience, vol. 24, no. 13, pp. 1397-1420, 2012.",
        "[3] C. Reiss, A. Tumanov, G. R. Ganger, R. H. Katz, and M. A. Kozuch, 'Heterogeneity and dynamicity of clouds at scale: Google trace analysis,' in Proc. 3rd ACM Symp. Cloud Comput. (SoCC), 2012, pp. 1-13.",
        "[4] A. d'Avila Garcez, M. Gori, L. C. Lamb, L. Serafini, M. Spranger, and S. N. Tran, 'Neural-symbolic computing: An effective methodology for principled learning and reasoning,' arXiv preprint arXiv:1905.06088, 2019.",
        "[5] Z. Shen, S. Subbiah, X. Gu, and J. Wilkes, 'CloudScale: Elastic resource scaling for multi-tenant cloud systems,' in Proc. 2nd ACM Symp. Cloud Comput. (SoCC), 2011, pp. 1-14.",
        "[6] F. Farahnakian, T. Pahikkala, P. Liljeberg, J. Plosila, N. T. Hieu, and H. Tenhunen, 'Energy-aware VM consolidation in cloud datacenters using reinforcement learning and sliding window,' in Proc. IEEE 7th Int. Conf. Cloud Comput. (CLOUD), 2014, pp. 312-319.",
        "[7] K. Cho et al., 'Learning phrase representations using RNN encoder-decoder for statistical machine translation,' in Proc. EMNLP, 2014, pp. 1724-1734.",
        "[8] M. Mao and M. Humphrey, 'A performance study on the VM startup time in the cloud,' in Proc. IEEE 5th Int. Conf. Cloud Comput. (CLOUD), 2012, pp. 423-430.",
    ]
    for r in refs:
        p_ref = doc.add_paragraph()
        p_ref.add_run(r)

    doc.save(DOCX_PATH)
    print(f"Generated DOCX report: {DOCX_PATH}")

if __name__ == "__main__":
    build_docx()
