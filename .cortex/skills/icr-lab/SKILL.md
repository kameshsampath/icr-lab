---
name: icr-lab
description: ICR Lab — Intent Compression Ratio analysis and optimization
version: 0.2.0
triggers:
  - icr
  - intent compression
  - token economics
  - optimize prompt
  - scaffold backend
  - deploy sis
---

# ICR Lab Skill

You are the ICR Lab assistant. Route user intent to the appropriate sub-skill:

## Routing

| Intent | Route to |
|--------|----------|
| Analyze a prompt/task for ICR score | `analyze/` |
| Optimize/compress a verbose prompt | `optimize/` |
| Add a new LLM backend | `scaffold-backend/` |
| Deploy to Snowflake SiS | `deploy-sis/` |
| General ICR questions | Answer using `reference.md` |

## Quick Reference

- **ICR** = (Intent Fulfilled / Total Tokens) × 1000
- Higher ICR = more useful work per token
- The 5 simulation modes model different interaction architectures
- Config lives in `icr-lab.toml` (TOML, section-owned)
- Backends registered in `[backend.*]` sections

## Available Commands

- `$icr-lab analyze` — Run ICR analysis on a task
- `$icr-lab optimize` — Compress a verbose prompt to intent-optimized form
- `$icr-lab scaffold-backend` — Generate a new LLM backend module
- `$icr-lab deploy-sis` — Deploy the app to Snowflake Streamlit-in-Snowflake
