# ICR Lab

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://icr-lab.streamlit.app/)

A companion demo for the article [**ICR: Measuring the Power of Intent**](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9).

The main demo is titled **ICR and Token Economics** — an interactive Streamlit simulator that shows how the same user intent produces wildly different token footprints depending on the interaction architecture.

## What It Demonstrates

- **Relative ICR Scores** — Normalized 0-100% comparison across interaction modes. The most efficient mode scores 100%; others are scored relative to it.
- **Token Amplification Factor** — How many extra tokens a less-efficient mode consumes for the same intent (e.g., "Verbose Prompting uses 7.0x more tokens").
- **Prompt Comparison** — Side-by-side view of verbose vs. intent-optimized prompts achieving identical outcomes.
- **Help / Glossary** — Built-in reference page explaining ICR, token amplification, relative scores, token economics, and why v1 uses simulation instead of live LLM calls.

## Why Simulation?

v1 uses deterministic simulation rather than live LLM calls because:

- **Reproducible** — Same inputs always produce the same visualization. No API variance.
- **No API keys required** — Runs fully local, zero dependencies on external services.
- **Fast iteration** — Instant results for 10 pre-built examples spanning Snowflake, Kubernetes, Terraform, Ansible, and general programming.

The simulation models realistic token growth patterns for each interaction mode based on observed patterns from real AI system usage.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install & Run

```bash
git clone https://github.com/kameshsampath/icr-lab.git
cd icr-lab

# Install dependencies with uv
uv sync

# Run the app
uv run streamlit run app/main.py
```

Opens at [http://localhost:8501](http://localhost:8501).

### Alternative (pip)

```bash
pip install streamlit plotly pandas
streamlit run app/main.py
```

## Usage

1. Select or enter a task in the sidebar
2. Choose simulation modes to compare
3. Click **Run Simulation**
4. Explore: ICR gauges, token comparison, cumulative growth, prompt comparison, interaction traces

## Simulation Modes

| Mode | Behavior | Token Efficiency |
|------|----------|-----------------|
| Verbose Prompting | Large prompts with repeated context | Lowest |
| Clarification Heavy | Multiple rounds with growing context | Low |
| Context-Aware | Structured requests with partial reuse | Moderate |
| Intent-Optimized | Single compressed intent expression | Highest |

## Project Structure

```
icr-lab/
├── app/
│   ├── main.py              # Streamlit dashboard (main page)
│   └── pages/help.py        # Help / Glossary page
├── simulations/engine.py    # Simulation logic for 4 modes
├── metrics/calculator.py    # ICR formula + cost calculations
├── visuals/charts.py        # Plotly chart builders
├── examples/
│   ├── catalog.py           # Full prompt examples per mode
│   └── sample_tasks.py      # Pre-built example tasks
├── .streamlit/config.toml   # Streamlit configuration
├── pyproject.toml           # uv project configuration
└── README.md
```

## Related Reading

ICR Lab is part of a broader exploration of intent-native software systems.

- [Infrastructure as Intent: The Field Velocity Blueprint](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
- [The Ghost in the Machine: Why AI Needs the Spirit of UML](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
- [Intent Driven Development: The Shift Developers Can't Ignore](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
- [Intent Compression Ratio: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
