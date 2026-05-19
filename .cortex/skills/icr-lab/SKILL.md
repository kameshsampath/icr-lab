---
name: icr-lab
description: "ICR Lab — simulate, analyze, compare, and optimize Intent Compression Ratio and token economics across interaction architectures. Use when: running ICR simulations, measuring token efficiency, comparing interaction modes, compressing prompts, benchmarking token costs, setting up config, scaffolding LLM backends, deploying to Snowflake SiS. Triggers: icr, intent compression, token economics, simulate tokens, compare modes, benchmark icr, measure efficiency, optimize prompt, compress prompt, scaffold backend, deploy sis, icr-lab setup, icr-lab configure, icr-lab init."
---

# ICR Lab Skill

You are the ICR Lab assistant. Detect user intent and route to the appropriate sub-skill.

## Intent Detection

| Intent | Trigger Phrases | Route |
|--------|----------------|-------|
| **SETUP** | "icr-lab setup", "icr-lab configure", "icr-lab init", "reset config", "fix config", "configure icr" | `setup/SKILL.md` |
| **ANALYZE** | "analyze icr", "simulate task", "compare modes", "benchmark", "run icr", "measure tokens", "evaluate efficiency", "icr score", "token analysis" | `analyze/SKILL.md` |
| **OPTIMIZE** | "optimize prompt", "compress prompt", "reduce tokens", "shorten prompt", "make concise", "tune prompt", "intent optimize" | `optimize/SKILL.md` |
| **SCAFFOLD** | "scaffold backend", "add backend", "new backend", "create backend", "register backend", "integrate llm" | `scaffold-backend/SKILL.md` |
| **DEPLOY** | "deploy sis", "deploy snowflake", "publish app", "ship to snowflake", "streamlit in snowflake" | `deploy-sis/SKILL.md` |

## Routing Rules

1. Match user message against trigger phrases (case-insensitive, partial match OK)
2. If matched -> load the corresponding sub-skill and follow its workflow
3. If ambiguous -> ask user to clarify intent
4. If general ICR question -> answer using `reference.md`

## Quick Reference

- **ICR** = (Intent Fulfilled / Total Tokens) x 1000
- Higher ICR = more useful work per token
- The 5 simulation modes model different interaction architectures
- Config lives in `icr-lab.toml` (TOML, section-owned, gitignored)
- Backends registered in `[backend.*]` sections

## Available Sub-Skills

- `$icr-lab setup` — Initialize or repair configuration
- `$icr-lab analyze` — Run ICR analysis on a task
- `$icr-lab optimize` — Compress a verbose prompt to intent-optimized form
- `$icr-lab scaffold-backend` — Generate a new LLM backend module
- `$icr-lab deploy-sis` — Deploy the app to Snowflake Streamlit-in-Snowflake

## Future: LMStudio Local Skill Matching

When LMStudio is added as a backend, use it for skill matching LLM calls
instead of consuming tokens on paid backends. Planned approach:

1. Embed the optimized task intent via `nomic-embed-text-v1.5` (`/v1/embeddings`)
2. Embed all skill descriptions from the catalog (cache embeddings)
3. Cosine similarity → top-k skill candidates (threshold >= 0.5)
4. Optional: rerank with a small Qwen model via `/v1/chat/completions`
5. LMStudio becomes the preferred backend for skill matching calls (free, local, fast)
