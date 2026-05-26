# ICR Lab

[![Open in Streamlit](https://img.shields.io/badge/Open%20in-Streamlit-red?logo=streamlit)](https://icr-lab.streamlit.app/)

A companion demo for the article [**ICR: Measuring the Power of Intent**](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9).

The main demo is titled **ICR and Token Economics** — an interactive Streamlit simulator that shows how the same user intent produces wildly different token footprints depending on the interaction architecture.

## What It Demonstrates

- **Relative ICR Scores** — Normalized 0-100% comparison across interaction modes. The most efficient mode scores 100%; others are scored relative to it.
- **Token Amplification Factor** — How many extra tokens a less-efficient mode consumes for the same intent (e.g., "Verbose Prompting uses 7.0x more tokens").
- **Output Compression Toggle** — Simulate Caveman-style output brevity to show that compression compounds with good architecture but doesn't replace it.
- **Assumption Accuracy Slider** — Control how accurate the model's inferences are in Assumption Led mode. Slide from 1.0 (perfect) to 0.0 (all wrong) to see how assumption quality drives correction loops and missed requirements.
- **Prompt Comparison** — Side-by-side view of verbose vs. intent-optimized prompts achieving identical outcomes.
- **Payload Generator** — Interactive page to build and copy the `/simulate` API request JSON and a ready-to-run cURL command.
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
3. Adjust **Assumption Accuracy** — affects Assumption Led mode (`ops_achieved = floor(ops × accuracy)`)
4. Optionally enter **Requirements** (pre-filled from catalog) to see a per-mode coverage grid
5. Click **Run Simulation**
6. Explore: ICR gauges, token comparison, cumulative growth, requirements coverage, prompt comparison, interaction traces
7. Use the **Payload Generator** page to build and copy a ready-to-run API request

## Simulation Modes

| Mode | Behavior | Token Efficiency |
|------|----------|-----------------|
| Verbose Prompting | Large prompts with repeated context | Lowest |
| Clarification Heavy | Multiple rounds with growing context | Low |
| Over Compressed | Ambiguous compressed prompt triggers correction loops | Variable |
| Context Aware | Structured requests with partial reuse | Moderate |
| Assumption Led | Agent infers missing context and executes; correction loops emerge when assumptions are wrong — controlled by `assumption_accuracy` | Moderate–Low |
| Intent Optimized | Single compressed intent expression | Highest |

## Project Structure

```
icr-lab/
├── app/
│   ├── main.py                     # Streamlit entry point (registers pages)
│   └── pages/
│       ├── home.py                 # Main simulator dashboard
│       ├── payload_generator.py    # API payload builder
│       └── help.py                 # Help / Glossary page
├── api/index.py                    # FastAPI /simulate endpoint
├── simulations/engine.py           # Simulation logic for 6 modes
├── metrics/calculator.py           # ICR formula + cost calculations
├── visuals/charts.py               # Plotly chart builders
├── examples/
│   ├── catalog.py                  # Full prompt examples per mode
│   └── sample_tasks.py             # Pre-built example tasks
├── .streamlit/config.toml          # Streamlit configuration
├── pyproject.toml                  # uv project configuration
└── README.md
```

## API

The simulation engine is also exposed as a REST API (`api/index.py`).

### Run the API

```bash
task api
# or:
uv run uvicorn api.index:app --reload
```

### `POST /simulate`

```json
{
  "task": "Deploy a connector with Snowflake Openflow",
  "operations": 12,
  "modes": ["Clarification Heavy", "Assumption Led", "Intent Optimized"],
  "requirements": ["connector installed", "schema mapped", "data flowing", "alerts configured"],
  "assumption_accuracy": 0.85
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `task` | string | required | Task description (≤ 2000 chars) |
| `operations` | int | auto | Number of operations; auto-derived from catalog when omitted |
| `modes` | string[] | all | Modes to simulate |
| `requirements` | string[] | `[]` | Requirements to map against `operations_achieved` |
| `assumption_accuracy` | float 0–1 | `0.85` | Fraction of ops achieved = `floor(ops × accuracy)` in Assumption Led mode |
| `mode_operations_achieved` | dict | `{}` | Override per-mode `operations_achieved` for demo scenarios |

Use the **Payload Generator** page in the app to build requests visually.

## Related Reading

ICR Lab is part of a broader exploration of intent-native software systems.

- [Infrastructure as Intent: The Field Velocity Blueprint](https://blogs.kameshs.dev/infrastructure-as-intent-the-field-velocity-blueprint-e6217ef30f14)
- [The Ghost in the Machine: Why AI Needs the Spirit of UML](https://blogs.kameshs.dev/the-ghost-in-the-machine-why-ai-needs-the-spirit-of-uml-0d8864e583e2)
- [Intent Driven Development: The Shift Developers Can't Ignore](https://blogs.kameshs.dev/intent-driven-development-the-shift-developers-cant-ignore-ef434f94d56c)
- [Intent Compression Ratio: Measuring the Power of Intent](https://blogs.kameshs.dev/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9)
- [Caveman](https://github.com/juliusbrussee/caveman) — Output token compression ("why use many token when few do trick")

## License

Apache License 2.0 — see [LICENSE](LICENSE).
