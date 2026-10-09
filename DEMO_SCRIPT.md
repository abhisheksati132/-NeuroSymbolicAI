# 5-MINUTE LIVE DEMO SCRIPT & VIVA DEFENSE GUIDE

**Course:** BCSE355L Cloud Architecture Design  
**Faculty In-Charge:** Prof. Padmavathy T (SCOPE, VIT)  
**Project:** Cloud Resource Allocation using Neuro-Symbolic AI  
**Team Members:**  
- Deepanshu Agarwal (24BCI0142)  
- Sanjay Giridhar K (24BCE0581)  
- Abhishek Sati (24BDS0199)  

---

## Part 1: Five-Minute Demo Walkthrough

### Preparation (30 seconds before demo)
Open two terminal tabs in the project directory:
```powershell
# Terminal 1: Launch the Interactive Web Dashboard
python src/dashboard/app.py
```
Open a browser and navigate to: `http://127.0.0.1:5000`

---

### Step 1: System Motivation & Problem Statement (Minute 1: 0:00 - 1:00)
> *"Good morning, Ma'am. In enterprise cloud datacenters, resource allocation faces a fundamental tension: we want to consolidate workloads to save energy and cost, but aggressive packing often pushes servers past safe 85% utilization thresholds, causing SLA violations and hypervisor thrashing.*
>
> *Traditional heuristics like First Fit and Best Fit are reactive—they pack servers blindly until failure. Pure neural networks predict load well, but act as black boxes with zero safety guarantees.*
>
> *Our project introduces a Neuro-Symbolic AI Allocator. We pair a PyTorch GRU demand forecaster with an explicit declarative symbolic rule engine. The neural component anticipates incoming bursts, while the symbolic component guarantees hard capacity safety bounds, SLA headrooms, and tenant isolation, generating auditable rule traces for 100% of decisions."*

---

### Step 2: Showcasing the Baseline Heuristic Failure (Minute 2: 1:00 - 2:00)
1. In the Dashboard dropdown, select **Best Fit [Baseline Heuristic]**.
2. Keep **Workload Size: 300**, **Seed: 42**, and click **Execute Simulation**.
3. Point to the KPI cards and explanation table:
> *"Notice that Best Fit quickly packs servers to 100% capacity. Look at the Hard Rule Violations card: it triggers over 200 hard-rule breaches! It repeatedly pushes servers above the 85% safety bound and colocates conflicting priority tenants on the same physical host, creating single points of failure."*

---

### Step 3: Demonstrating the Proposed Neuro-Symbolic Allocator (Minute 3: 2:00 - 3:15)
1. In the dropdown, switch to **Neuro-Symbolic [Proposed GRU + Symbolic Rules]**.
2. Click **Execute Simulation**.
3. Point to the updated telemetry cards and live charts:
> *"Now look at the proposed Neuro-Symbolic allocator on the exact same workload:*
> - *Hard Rule Violations drop to exactly ZERO (0.0). No server ever breaches the 85% safety bound.*
> - *Datacenter Power and Energy are minimized (saving over 5%–14% energy) through our symbolic packing bonus (Rule R4).*
> - *Decision Latency remains sub-millisecond (0.88 ms), easily meeting real-time cloud dispatch requirements.*
> - *Rule Explainability is 100%: every single allocation produces an auditable trace."*

---

### Step 4: Live Rule Trace & Audit Table Inspection (Minute 4: 3:15 - 4:15)
1. Scroll down to the **Auditable Symbolic Decision & Rule Explanation Log** table.
2. Show a specific row to the faculty:
> *"Here in the live audit log, every task assignment shows why a host was selected:*
> - *Rule R1 verified that post-allocation CPU/RAM utilization remained safely below 85%.*
> - *For Priority 3 critical tasks, Rule R2 verified that at least 25% safety headroom remained.*
> - *Rule R3 checked failure domains to prevent colocating tasks from the same tenant.*
> - *Rule R6 incorporated the GRU neural forecast: when the model predicted cluster saturation, it reserved high-capacity Compute and Memory Optimized nodes specifically for incoming critical requests."*

---

### Step 5: Wrap-up & Benchmark Summary (Minute 5: 4:15 - 5:00)
> *"We benchmarked this across 5 random seeds up to 2000 tasks. In our ablation study, disabling symbolic rules (Pure Neural) triggered 474 hard violations per run, while disabling the neural forecast increased queue wait times. The neuro-symbolic fusion provides the ideal sweet spot: statistical predictive foresight backed by hard deterministic mathematical guarantees."*

---

## Part 2: Likely Viva Questions & High-Scoring Answers

### Q1: What makes this "Neuro-Symbolic" instead of just a heuristic rule engine?
**Answer:**
> *"A purely symbolic engine is static and reactive; it has no concept of temporal patterns or future arrivals. In our system, the neural component is a 2-layer PyTorch GRU that takes a sliding historical window of 12 steps and predicts future aggregate cluster demand $(\hat{D}_{\text{cpu}}, \hat{D}_{\text{ram}})$ on held-out data with an MAE of 15.8 vCPUs. This statistical forecast feeds directly into the symbolic engine via Rule R6: when the neural model forecasts cluster saturation above 75%, the symbolic engine dynamically adjusts its candidate scoring, reserving specialized nodes for high-priority tasks and waking standby hosts in advance. It is a bidirectional coupling of statistical prediction and deterministic constraint satisfaction."*

---

### Q2: Why did traditional heuristics (Round Robin, Best Fit) have a lower SLA violation rate on small workloads than your allocator?
**Answer:**
> *"That is an important, honest trade-off in cloud scheduling. Heuristics like Best Fit achieve an artificially low waiting time because they cheat safety: they shove tasks onto hosts that are already at 90% or 98% utilization, ignoring safety margins and causing over 300 hard-rule violations. In a real hypervisor, running at 98% CPU causes severe CPU throttling, cache thrashing, and packet loss. Our allocator strictly enforces an 85% safety bound (Rule R1). When the cluster is congested, it holds tasks in the queue rather than endangering active production nodes. Once workload scales up to 1000 tasks, the heuristic approach collapses completely (85% SLA violations), whereas our allocator achieves 57% SLA violations and saves 14% energy."*

---

### Q3: What happens when all active physical hosts violate the hard rules?
**Answer:**
> *"Our algorithm implements a deterministic two-tier fallback: First, if no active host can accept the task without breaching the 85% utilization threshold or anti-affinity rules, the allocator inspects inactive standby hosts. If an idle host can safely fit the task, it powers it on (state transition from standby to active). If even the standby hosts cannot safely accommodate the request, the task is held in the priority queue rather than violating physical safety constraints. This guarantees zero hard-rule breaches."*

---

### Q4: How is server power and energy calculated in your simulator?
**Answer:**
> *"We implement the empirical linear-utilization power curve established by Fan, Weber, and Barroso in their seminal Google ISCA 2007 paper:
> $$P_h(t) = P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \times u_h(t)$$
> where $u_h(t) = \max(u_{\text{CPU}}, u_{\text{RAM}})$. For example, on our General Purpose GP-4 nodes, idle power is 80 W and peak power is 250 W. When consolidated into low-power standby mode, nodes dissipate only 10 W. Total energy is integrated over discrete 60-second simulation intervals and reported in kilowatt-hours (kWh)."*

---

### Q5: How do you guarantee multi-tenant fault tolerance?
**Answer:**
> *"Through Rule R3 (Anti-Affinity Policy). For any mission-critical task (Priority 3), the symbolic engine queries the active tasks currently hosted on each candidate node. If the candidate node already hosts a Priority 3 task belonging to the same tenant ID, Rule R3 rejects that host. This ensures that a single physical host crash never causes a correlated multi-task failure for any tenant."*

---

### Q6: What is the computational complexity and decision latency of your allocator?
**Answer:**
> *"The GRU neural inference executes in constant time $O(1)$ over a fixed $12 \times 2$ input window. The symbolic rule engine evaluates $M$ physical hosts across 6 explicit predicate checks, giving $O(M)$ time complexity. In our empirical measurements, the average decision time per task was $0.886 \pm 0.029$ milliseconds—over 100 times faster than typical cloud scheduling deadlines (which operate on 100 ms to 1 second control loops)."*
