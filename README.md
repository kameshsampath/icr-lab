# ICR Lab

[![Open in Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-red?logo=streamlit)](https://icr-lab.streamlit.app/)

A companion demo for the article [**ICR: Measuring the Power of Intent**](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9).

An interactive Streamlit simulator that shows how the same user intent produces wildly different token footprints depending on the interaction architecture.

## What It Demonstrates

- **Relative ICR Scores** — Normalized 0-100% comparison across interaction modes
- **Token Amplification Factor** — How many extra tokens a less-efficient mode consumes for the same intent
- **Output Compression Toggle** — Simulate Caveman-style output brevity
- **Live Optimization** — Connect a real LLM backend to compress prompts
- **Prompt Comparison** — Side-by-side verbose vs. intent-optimized prompts

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended)
- [go-task](https://taskfile.dev/) (optional, for `task` commands)
- Snowflake CLI (optional, for cortex backend)

### Install & Run

```bash
git clone https://github.com/kameshsampath/icr-lab.git
cd icr-lab

# Install dependencies
task setup        # or: uv sync

# Launch the app
task serve        # or: uv run icr-lab serve
```

Opens at [http://localhost:8501](http://localhost:8501).

### CLI Commands

```bash
# Run ICR analysis on a task
uv run icr-lab analyze "Deploy payment service with autoscaling"

# Optimize a prompt
uv run icr-lab optimize "Your verbose prompt here..."

# Launch Streamlit UI
uv run icr-lab serve
```

### Live Mode (Optional)

Edit `icr-lab.toml` to configure a live LLM backend:

```toml
[backend]
default = "cortex"

[backend.cortex]
model = "llama3.1-8b"
connection = "default"
```

To add a third-party backend (e.g., LM Studio), run `$icr-lab scaffold-backend` in Cortex Code.

Run `task configure` to validate your setup, or use `$icr-lab setup` in Cortex Code.

### Deploy to Snowflake

Run `$icr-lab deploy-sis` in Cortex Code to ship the app to Streamlit-in-Snowflake.

## Simulation Modes

| Mode | Behavior | Token Efficiency |
|------|----------|-----------------|
| Verbose Prompting | Large prompts with repeated context | Lowest |
| Clarification Heavy | Multiple rounds with growing context | Low |
| Over-Compressed | Ambiguous prompt triggers correction loops | Variable |
| Context-Aware | Structured requests with partial reuse | Moderate |
| Intent-Optimized | Single compressed intent expression | Highest |

## Project Structure

```
icr-lab/
├── app/
│   ├── main.py              # Streamlit entry point
│   ├── _cli.py              # CLI (analyze, optimize, serve)
│   └── pages/
│       ├── home.py          # Main dashboard
│       └── help.py          # Help / Glossary
├── backends/
│   ├── __init__.py          # Backend registry
│   ├── base.py              # LLMBackend protocol
│   ├── config.py            # Config loader + validation
│   ├── simulation.py        # Deterministic simulation backend
│   └── cortex.py            # Snowflake Cortex backend
├── simulations/engine.py    # Simulation logic for 5 modes
├── metrics/calculator.py    # ICR formula + cost calculations
├── visuals/charts.py        # Plotly chart builders
├── examples/                # Sample tasks + prompt catalog
├── icr-lab.toml             # Local config (gitignored)
├── Taskfile.yml             # Task runner commands
├── pyproject.toml           # Project metadata + deps
└── README.md
```

## Development

```bash
task lint         # Check code style
task format       # Auto-format
task configure    # Validate config + test Snowflake connection
```

## Related Reading

- [Infrastructure as Intent: The Field Velocity Blueprint](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
- [The Ghost in the Machine: Why AI Needs the Spirit of UML](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
- [Intent Driven Development: The Shift Developers Can't Ignore](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
- [Intent Compression Ratio: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
- [Caveman](https://github.com/juliusbrussee/caveman) — Output token compression

## License

Apache License 2.0 — see [LICENSE](LICENSE).
