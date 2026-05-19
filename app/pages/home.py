"""Home — ICR and Token Economics dashboard."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.sample_tasks import SAMPLE_TASKS, get_operations_count
from metrics.calculator import compute_metrics, compute_savings
from simulations.engine import SIMULATION_MODES, run_simulation, apply_output_compression
from visuals.charts import (
    cumulative_growth_chart,
    efficiency_dataframe,
    icr_gauge_chart,
    token_comparison_chart,
)

# --- Sidebar controls ---
with st.sidebar:
    st.title("ICR Lab")
    st.caption("Intent Compression Ratio & Token Economics")

    st.divider()

    # Example task selection
    example_choice = st.selectbox(
        "Example Tasks",
        options=["(custom)"] + SAMPLE_TASKS,
        index=0,
        help="Select a pre-built task or write your own below",
    )

    # Custom task input
    if example_choice == "(custom)":
        task_input = st.text_area(
            "Task Description",
            placeholder="e.g., Deploy payment service with autoscaling and observability",
            height=100,
        )
    else:
        task_input = st.text_area(
            "Task Description",
            value=example_choice,
            height=100,
        )

    st.divider()

    # Mode selection
    selected_modes = st.multiselect(
        "Simulation Modes",
        options=list(SIMULATION_MODES.keys()),
        default=list(SIMULATION_MODES.keys()),
        help="Select which interaction modes to compare",
    )

    st.divider()

    # Output compression toggle
    st.markdown("**Output Compression**")
    apply_compression = st.toggle(
        "Caveman-style compression",
        value=False,
        help="Simulates terse AI responses (~35% output token reduction). Shows how output brevity interacts with interaction architecture.",
    )
    if apply_compression:
        compression_factor = st.slider(
            "Compression factor",
            min_value=0.30, max_value=1.0, value=0.65, step=0.05,
            help="1.0 = no compression, 0.65 = Caveman default (~35% reduction)",
        )
    else:
        compression_factor = 1.0

    st.divider()

    # Run button
    run_clicked = st.button(
        "Run Simulation",
        type="primary",
        width="stretch",
        disabled=not task_input or not selected_modes,
    )

# --- Main Content ---
col_title, col_nav = st.columns([4, 1])
with col_title:
    st.header("ICR and Token Economics")
with col_nav:
    st.page_link("pages/help.py", label="Help & Glossary", icon="📖")

st.markdown(
    "*Same intent. Different interaction architecture. Different token economics.*"
)
st.markdown(
    "ICR Lab simulates five interaction modes and compares their token footprint:"
)
st.markdown(
    "- **Verbose Prompting** — long, detailed prompts with repeated context\n"
    "- **Clarification Heavy** — multiple back-and-forth rounds\n"
    "- **Context-Aware** — structured requests with partial reuse\n"
    "- **Intent-Optimized** — single compressed intent expression\n"
    "- **Over-Compressed** — too terse, triggers correction loops that amplify tokens"
)

# ICR Formula
with st.expander("📐 ICR Formula", expanded=True):
    st.latex(
        r"\text{ICR} = \frac{\text{Intent Fulfilled}}{\text{Total Tokens}} \times 1000"
    )
    st.caption("Higher ICR = more useful work completed per token consumed.")

if not task_input:
    st.info(
        "Enter a task description in the sidebar and click **Run Simulation** to begin."
    )
    st.stop()

# Invalidate stale session state on code changes
_METRICS_VERSION = 8
if st.session_state.get("_metrics_version") != _METRICS_VERSION:
    for key in ["results", "metrics", "savings", "task", "operations"]:
        st.session_state.pop(key, None)
    st.session_state["_metrics_version"] = _METRICS_VERSION

if not run_clicked and "results" not in st.session_state:
    st.info("Click **Run Simulation** to compare interaction modes.")
    st.stop()

# Run simulation
if run_clicked:
    operations = get_operations_count(task_input)
    results = run_simulation(task_input, operations, selected_modes)
    if compression_factor < 1.0:
        results = apply_output_compression(results, compression_factor)
    metrics = compute_metrics(results)
    savings = compute_savings(metrics)

    # Store in session state
    st.session_state["results"] = results
    st.session_state["metrics"] = metrics
    st.session_state["savings"] = savings
    st.session_state["task"] = task_input
    st.session_state["operations"] = operations

# Retrieve from session state
results = st.session_state["results"]
metrics = st.session_state["metrics"]
savings = st.session_state["savings"]
task = st.session_state["task"]
operations = st.session_state["operations"]

# --- Task Context ---
st.markdown(f"**Task:** {task}")
st.markdown(
    f"**Intent Fulfilled (ICR baseline):** {operations} ops compressed into 1 intent"
)

st.divider()

# --- Top-level Metrics ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Best ICR Score",
        value=f"{savings['best_icr']}",
        help="Intent Compression Ratio — higher means more efficient token usage",
    )

with col2:
    st.metric(
        label="Token Savings",
        value=f"{savings['token_savings_pct']}%",
        help="Tokens saved by best mode vs worst mode",
    )

with col3:
    st.metric(
        label="Max Amplification",
        value=f"{savings['worst_amplification']:.1f}x",
        help="Token waste multiplier of the least efficient mode",
    )

with col4:
    st.metric(
        label="Cost Savings",
        value=f"{savings['cost_savings_pct']}%",
        help="Estimated cost reduction from optimized intent",
    )

# --- Amplification callout ---
worst_mode = max(metrics, key=lambda m: m.token_amplification)
if worst_mode.token_amplification > 1.0:
    st.info(
        f"**{worst_mode.mode}** uses **{worst_mode.token_amplification:.1f}x** more tokens "
        f"than the most efficient mode for the same intent."
    )

# --- Compression insight ---
if compression_factor < 1.0:
    st.success(
        f"**Output compression ({int((1 - compression_factor) * 100)}% reduction) applied.** "
        f"Architecture gap remains **{worst_mode.token_amplification:.1f}x**. "
        f"Compression helps — but interaction architecture is the bigger lever."
    )

st.divider()

# --- Relative ICR Scores ---
st.subheader("Relative ICR Scores")
best_mode = max(metrics, key=lambda m: m.icr_score)
st.success(f"**Best: {best_mode.mode}** — ICR score {best_mode.icr_score:.2f}")
st.write("")
st.latex(
    r"\text{Relative ICR} = \frac{\text{Mode ICR}}{\text{Best Mode ICR}}"
    r"\quad \Rightarrow \quad 1.0 = \text{most efficient},\ 0.5 = 2\times\text{ more tokens per op}"
)
st.write("")
st.plotly_chart(icr_gauge_chart(metrics), width="stretch")

# --- Token Comparison ---
st.subheader("Token Comparison")
st.plotly_chart(token_comparison_chart(metrics), width="stretch")

# --- Cumulative Growth + Efficiency Table ---
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Cumulative Token Growth")
    st.plotly_chart(cumulative_growth_chart(results), width="stretch")
    st.caption(
        "Clarification-heavy systems may look conversationally helpful, "
        "but each round expands the token footprint."
    )

with col_right:
    st.subheader("Efficiency Metrics")
    df = efficiency_dataframe(metrics)
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Relative ICR": st.column_config.ProgressColumn(
                "Relative ICR",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

# --- Prompt Comparison ---
st.divider()
st.subheader("Prompt Comparison")
st.caption("Side-by-side: how the same intent looks at different compression levels")

# Find verbose and optimized results
verbose_result = next((r for r in results if r.mode == "Verbose Prompting"), None)
optimized_result = next((r for r in results if r.mode == "Intent-Optimized"), None)

if verbose_result and optimized_result:
    col_v, col_o = st.columns(2)

    with col_v:
        st.markdown("**Verbose Prompting**")
        verbose_prompt = (
            verbose_result.rounds[0].prompt_text if verbose_result.rounds else ""
        )
        if verbose_prompt:
            st.error(verbose_prompt)
            st.caption(f"~{len(verbose_prompt.split())} words")

    with col_o:
        st.markdown("**Intent-Optimized**")
        opt_prompt = optimized_result.optimized_prompt
        if opt_prompt:
            st.success(opt_prompt)
            st.caption(f"~{len(opt_prompt.split())} words")

    if verbose_prompt and opt_prompt:
        reduction = round(
            (1 - len(opt_prompt.split()) / len(verbose_prompt.split())) * 100
        )
        st.metric("Word Reduction", f"{reduction}%", help="Fewer words, same outcome")
elif optimized_result:
    st.markdown("**Intent-Optimized Prompt:**")
    st.success(optimized_result.optimized_prompt)

st.caption("Higher ICR does not mean less intent. It means less redundant expression.")

# --- Interaction Traces ---
st.divider()
st.subheader("Interaction Traces")

for result in results:
    with st.expander(
        f"{result.mode} — {len(result.rounds)} round(s), {result.total_tokens:,} total tokens"
    ):
        for r in result.rounds:
            st.markdown(
                f"**Round {r.round_number}:** {r.description}  \n"
                f"↳ Input: {r.input_tokens:,} | Output: {r.output_tokens:,} | "
                f"Cumulative: {r.cumulative_tokens:,}"
            )
            if r.prompt_text:
                st.code(r.prompt_text, language=None)

        # Show optimized alternative for non-optimal modes
        if result.mode != "Intent-Optimized" and result.optimized_prompt:
            st.divider()
            st.markdown("**Intent-Optimized Alternative:**")
            st.success(result.optimized_prompt)
