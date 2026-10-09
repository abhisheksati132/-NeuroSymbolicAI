# ASSUMPTIONS & DESIGN CONSTRAINTS

**Project:** Cloud Resource Allocation using Neuro-Symbolic AI  
**Course:** BCSE355L Cloud Architecture Design (SCOPE, Faculty: Padmavathy T)  
**Team Members:** Deepanshu Agarwal (24BCI0142), Sanjay Giridhar K (24BCE0581), Abhishek Sati (24BDS0199)  

---

### 1. Workload Trace Selection
- **Context:** Standard production traces such as Google Cluster Trace (2011/2019) or Bitbrains contain tens to hundreds of gigabytes of raw task events and require external cloud storage or specialized big data parsers that are not feasible for rapid, standalone, offline execution.
- **Decision:** As permitted by Rule 3, we utilize a strictly labeled **Synthetic Cloud Workload Generator** (`/src/simulator/workload.py`). The synthetic workload models key real-world datacenter dynamics:
  - Sinusoidal diurnal arrival trends (mimicking daily peak and off-peak business hours).
  - Poisson distributed job inter-arrival bursts.
  - Multi-tier task profiles: Web Microservices (CPU-intensive, short-lived), Batch Analytics (heavy CPU/RAM, long duration), and Real-time Processing (strict SLA, high priority).
  - Explicit SLA latency deadlines and priority assignments ($P \in \{1, 2, 3\}$).
- **Transparency:** The workload is explicitly documented as synthetic in all figures, tables, and the final report. No synthetic data is falsely attributed to real traces.

---

### 2. Physical Infrastructure & Heterogeneity Model
- **Datacenter Topology:** A private cloud or virtualized edge cluster consisting of heterogeneous physical compute hosts.
- **Host Flavors:**
  - `General Purpose (GP-4)`: 16 vCPUs, 64 GB RAM, Peak Power 250 W, Idle Power 80 W, Cost $0.40/hr.
  - `Compute Optimized (CO-4)`: 32 vCPUs, 64 GB RAM, Peak Power 380 W, Idle Power 110 W, Cost $0.65/hr.
  - `Memory Optimized (MO-4)`: 16 vCPUs, 128 GB RAM, Peak Power 310 W, Idle Power 95 W, Cost $0.75/hr.
- **Safety Headroom Threshold:** Hosts are constrained to not exceed an 85% safe utilization threshold for CPU and RAM to prevent hypervisor thrashing and tail-latency degradation.

---

### 3. Power and Energy Model
- Server power dissipation is modeled using the empirical linear-utilization power curve validated by Fan, Weber, and Barroso (2007):
  $$P(u) = P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \times u$$
  where $u = \max(u_{\text{CPU}}, u_{\text{RAM}})$ represents host resource utilization.
- Unallocated/idle hosts can transition to low-power standby mode ($P_{\text{standby}} = 10\text{ W}$) if consolidated.

---

### 4. Neural Demand Forecaster
- **Architecture:** PyTorch Recurrent / Gated Recurrent Unit (GRU) or Multi-Layer Perceptron (MLP) sequence predictor.
- **Input:** Sliding historical utilization window (past 12 steps).
- **Target:** Next-step upcoming aggregate cluster CPU and RAM demand.
- **Evaluation:** Evaluated on held-out temporal test splits using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).

---

### 5. Symbolic Engine & Explainability
- **Rules:**
  - `R1 [Capacity Bound]`: Host post-allocation CPU and RAM $\le 85\%$.
  - `R2 [SLA Headroom]`: High-priority tasks ($P=3$) require at least 25% host headroom remaining.
  - `R3 [Anti-Affinity]`: High-priority tasks from identical tenants cannot be co-located on the same physical host to avoid single-point failure.
  - `R4 [Energy Consolidation]`: Prefer packing underutilized active hosts before powering on standby nodes.
  - `R5 [Proactive Scale-out]`: If the neural demand forecast predicts saturation ($>80\%$) in the upcoming window, reserve or wake additional host capacity in advance.
- **Explainability:** 100% of allocation decisions produce an auditable rule trace describing which rule evaluated, accepted, or rejected each host candidate.

---

### 6. Experimental Rigor and Determinism
- In accordance with Absolute Rule 2, each experiment is executed across at least five distinct, fixed pseudo-random seeds ($42, 43, 44, 45, 46$).
- Results report mean and standard deviation ($\mu \pm \sigma$). All numerical values in the final report, tables, and charts are generated strictly by post-processing scripts from `/results` raw CSV files.
