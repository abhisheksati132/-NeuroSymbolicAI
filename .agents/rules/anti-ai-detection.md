# Academic Humanizer & Anti-AI-Detection Rule

This rule governs all academic report writing, paper generation, and technical documentation in this repository to prevent false-positive flags on Turnitin, GPTZero, CopyLeaks, and other AI-writing detectors.

## 1. Core Principles of Human Technical Prose

### A. High Burstiness (Sentence Length Variation)
- Never write three consecutive sentences of similar length (e.g., 20–25 words each).
- Alternate intentionally between:
  - Very short, punchy statements (4–8 words): *"Heuristics cheat. They pack boiling servers."* or *"Safety comes first."*
  - Moderate explanatory sentences (12–18 words).
  - Longer, compound technical descriptions (25–35 words) explaining mechanisms, equations, or hardware trade-offs.

### B. Active First-Person Engineering Perspective
- Write like a real student engineering team explaining what they designed, coded, and observed.
- Use direct active voice:
  - *"In our BCSE355L project, we designed..."* (NOT *"A framework is designed..."*)
  - *"We observed that First Fit caused 306 hard violations..."* (NOT *"It was observed that..."*)
  - *"Our team tuned the GRU learning rate to 0.005 because 0.01 diverged during early epochs."*

### C. Grounding in Real Hardware, Lab Quirks, and Implementation Choices
- Mention exact empirical choices made during implementation:
  - The 60-second discrete simulation tick.
  - The 12-step sliding history buffer capturing exactly 12 minutes of traffic history.
  - Hardware specifications from `results/system_config.json` (Intel Core i5, Python 3.14, AWS EC2 Ubuntu in Stockholm).
  - The Linux hypervisor cgroups 85% safety boundary rationale.

---

## 2. Strict AI Vocabulary Blacklist

The following words and phrases are banned from all technical sections:

| Banned AI Marker Words | Natural Human Replacements |
| :--- | :--- |
| *moreover, furthermore, in addition* | *also, on top of that, additionally, we also noticed* |
| *cohesive, holistic, comprehensive* | *complete, unified, combined, practical* |
| *paramount, pivotal, crucial* | *essential, vital, key, needed* |
| *testament, tapestry, realm* | *proof, evidence, domain, area* |
| *underscores, highlights, delves into* | *shows, demonstrates, explores, we examined* |
| *seamlessly, effortlessly* | *automatically, directly, reliably* |
| *it is worth noting that / it should be noted* | *(delete completely or state directly)* |
| *in conclusion, to summarize* | *in short, overall, finally, to wrap up* |

---

## 3. Structural & Formatting Invariants
- Preserve all mathematical formulas (native OMML equations, LaTeX math).
- Preserve all authentic empirical numbers across 5 seeds from `/results`.
- Preserve all 2023–2024 citations and IEEE numbered format.
- Preserve all figure and table numbering.
