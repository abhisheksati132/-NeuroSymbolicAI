---
name: anti-ai-academic-writing
description: Rewrites technical and academic papers into natural, human student-engineer voice with high burstiness and perplexity to bypass AI writing detectors (Turnitin, GPTZero, CopyLeaks) while preserving mathematical models, experimental numbers, and citations.
---

# Anti-AI Academic Writing Skill

Use this skill when generating, editing, or rewriting academic reports, IEEE conference papers, case studies, or thesis chapters that must pass institutional AI-detection filters (Turnitin, CopyLeaks, GPTZero) with a score under 5%.

## Core Humanization Techniques

### 1. Vary Sentence Lengths Dramatically (Burstiness)
AI detectors flag paragraphs where every sentence has a similar token count. Break this pattern:
- **Lead with a short, punchy sentence:** *"Heuristics pack servers blindly."* (4 words)
- **Follow with an explanatory clause:** *"Because greedy algorithms inspect only the immediate tick, they shove bursty tasks onto nodes that are already baking at 90% load."* (20 words)
- **Follow with an engineering detail:** *"During our testing, this caused 320 hard violations."* (8 words)

### 2. Infuse First-Person Active Voice & Team Decision History
- AI uses passive, impersonal declarations (*"The proposed framework is evaluated..."*).
- Replace with direct student engineering prose:
  - *"We evaluated our allocator across five fixed random seeds..."*
  - *"In our BCSE355L lab runs, we noticed..."*
  - *"Our team selected the 85% limit because modern Linux hypervisors begin aggressive CPU throttling when cgroups utilization crosses this line."*

### 3. Strip All Formulaic AI Transitions
- Eliminate: *Moreover, Furthermore, Delve, In conclusion, Testament, Tapestry, Paramount, Underscores, Cohesive, Seamlessly, Plethora, Nuanced*.
- Use clean, colloquial-academic transitions: *Also, At the same time, But in practice, To solve this, We found that, Specifically*.

### 4. Ground in Physical System Artifacts
- Reference real system files: `system_config.json`, `results/experiment_a_raw.csv`.
- Mention real hardware parameters: Intel CPU clock, RAM limits, 60-second discrete clock, AWS EC2 instance in Stockholm (`eu-north-1`).
- Mention actual tuning hurdles: *"We initially tested a learning rate of 0.01 for the GRU model, but the validation loss fluctuated; reducing it to 0.005 stabilized convergence."*

### 5. Academic Rigor Preserved
- Never dilute mathematical equations or theorem statements.
- Never alter empirical values from `/results`.
- Keep verified literature citations intact.
