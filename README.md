# ICR Lab

An interactive lab for exploring **Intent Compression Ratio** and **token economics** in AI systems.

> Better intent expression reduces unnecessary token consumption.

## What is Intent Compression Ratio (ICR)?

Intent Compression Ratio measures how much execution complexity is collapsed into intent. From the [reference article](https://medium.com/@kameshsampath/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9):

```
ICR = Total Operations / Intent Expressions
```

A system with an ICR of 1 is just a wrapper. A system with an ICR of 12 is an architectural partner.

For example, "Deploy a connector with Snowflake Openflow" compresses 12 distinct operations (user creation, role grants, network policies, auth policies, token generation, etc.) into a single intent expression.

## Token Amplification

Token amplification is the inverse problem: how poor interaction architecture creates token waste.

When developers interact with AI systems using:
- **Verbose prompting** — full context dumps repeated each turn
- **Clarification loops** — many rounds with growing context windows
- **Unstructured requests** — vague intents requiring back-and-forth

...the total tokens consumed can be **4-8x** what's needed with well-compressed intent.

**Token Amplification Factor** = Total Tokens Used / Minimum Tokens Needed

## The Connection

In this lab, we adapt ICR to token economics:

```
ICR Score = (Operations Achieved / Total Tokens) × 1000
```

Higher ICR Score = more operations achieved per token spent = better intent compression.

## Screenshots

*Run the app to see interactive visualizations comparing 4 interaction modes.*

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install & Run

```bash
# Clone the repository
git clone https://github.com/kameshsampath/icr-lab.git
cd icr-lab

# Install dependencies with uv
uv sync

# Run the app
uv run streamlit run app/main.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

### Alternative (pip)

```bash
pip install streamlit plotly pandas
streamlit run app/main.py
```

## Usage

1. **Select or enter a task** in the sidebar (e.g., "Deploy payment service with autoscaling and observability")
2. **Choose simulation modes** to compare
3. **Click "Run Simulation"** to see the results
4. **Explore the dashboard** — token comparison charts, cumulative growth, ICR gauges, and per-mode interaction traces

## Simulation Modes

| Mode | Behavior | Token Efficiency |
|------|----------|-----------------|
| Verbose Prompting | Large prompts with repeated explanations | Lowest |
| Clarification Heavy | Multiple rounds with growing context | Low |
| Context-Aware | Partial context reuse, structured requests | Moderate |
| Intent-Optimized | Single compressed intent expression | Highest |

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repository
5. Set the main file path to `app/main.py`
6. Click **Deploy**

## Project Structure

```
icr-lab/
├── app/
│   └── main.py              # Streamlit dashboard
├── simulations/
│   └── engine.py            # Simulation logic for 4 modes
├── metrics/
│   └── calculator.py        # ICR formula + cost calculations
├── visuals/
│   └── charts.py            # Plotly chart builders
├── examples/
│   └── sample_tasks.py      # Pre-built example tasks
├── pyproject.toml            # uv project configuration
└── README.md
```

## Reference

- [ICR: Measuring the Power of Intent](https://medium.com/@kameshsampath/intent-compression-ratio-measuring-the-power-of-intent-ceb6faf2e2f9) — Kamesh Sampath

## License

MIT
