"""Home — ICR and Token Economics dashboard."""

import math
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from examples.catalog import get_operation_commands  # noqa: E402
from examples.sample_tasks import SAMPLE_TASKS, get_operations_count  # noqa: E402
from metrics.calculator import compute_metrics, compute_savings  # noqa: E402
from simulations.engine import (  # noqa: E402
    SIMULATION_MODES,
    apply_output_compression,
    run_simulation,
)
from visuals.charts import (  # noqa: E402
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
        options=["(custom)"] + sorted(SAMPLE_TASKS),
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

    # Mode selection — pills are more compact than multiselect in a narrow sidebar
    __simulation_opts = sorted(SIMULATION_MODES.keys())

    selected_modes = st.pills(
        "Simulation Modes",
        options=__simulation_opts,
        default=__simulation_opts,
        format_func=lambda x: x.replace("-", " "),
        selection_mode="multi",
        help="Select which interaction modes to compare",
    )

    st.divider()

    # Assumption accuracy slider
    st.markdown("**Assumption Accuracy**")
    assumption_accuracy = st.slider(
        "Model accuracy on assumptions",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.05,
        help=(
            "Only affects Assumption Led mode. "
            "1.0 = perfect assumptions (0 wrong), "
            "0.0 = all assumptions wrong. "
            "Try 0.85 for a strong model or 0.60 for a mid-tier model."
        ),
    )

    st.divider()

    # Requirements — pre-filled from catalog, editable by user
    st.markdown("**Requirements**")
    _catalog_reqs = get_operation_commands(task_input) if task_input else []
    _default_reqs = "\n".join(_catalog_reqs)
    requirements_text = st.text_area(
        "One requirement per line",
        value=_default_reqs,
        height=120,
        key=f"reqs_{task_input[:60] if task_input else ''}",
        help="Pre-filled from the task catalog. Add, remove, or edit as needed.",
    )
    requirements_list = [r.strip() for r in requirements_text.splitlines() if r.strip()]

    st.divider()

    # Output compression toggle (secondary control — placed last)
    st.markdown("**Output Compression**")
    apply_compression = st.toggle(
        "Caveman-style compression",
        value=False,
        help="Simulates terse AI responses (~35% output token reduction). Shows how output brevity interacts with interaction architecture.",
    )
    if apply_compression:
        compression_factor = st.slider(
            "Compression factor",
            min_value=0.30,
            max_value=1.0,
            value=0.65,
            step=0.05,
            help="1.0 = no compression, 0.65 = Caveman default (~35% reduction)",
        )
    else:
        compression_factor = 1.0

    st.divider()
    run_clicked = st.button(
        "Run Simulation",
        type="primary",
        width="stretch",
        disabled=not task_input or not selected_modes,
    )

    # Live status badge — shown on Run Simulation click and updates on slider
    if (
        task_input
        and "Assumption Led" in (selected_modes or [])
        and (run_clicked or "results" in st.session_state)
    ):
        from simulations.engine import _task_complexity  # noqa: PLC0415

        _c = _task_complexity(task_input)
        _total_a = 1 + (_c % 3)
        _wrong = min(math.ceil(_total_a * (1 - assumption_accuracy)), _total_a)
        _rounds = 1 + (_wrong * 2 if _wrong > 0 else 0)
        _ops_preview = st.session_state.get("operations")
        _ops_achieved = (
            math.floor(_ops_preview * assumption_accuracy) if _ops_preview else None
        )
        _ops_part = (
            f" &nbsp;·&nbsp; <b>{_ops_achieved}/{_ops_preview}</b> ops"
            if _ops_achieved is not None
            else ""
        )
        st.markdown(
            f"<p style='font-size:0.78rem;opacity:0.7;margin-top:0.2rem;'>"
            f"<b>{_wrong}/{_total_a}</b> wrong"
            f" &nbsp;·&nbsp; <b>{_rounds}</b> round(s)"
            f"{_ops_part}"
            f" &nbsp;·&nbsp; <b>{int(assumption_accuracy * 100)}%</b> accurate"
            f"</p>",
            unsafe_allow_html=True,
        )

# --- Global style tweaks ---
st.markdown(
    """
    <style>
    /* Slightly smaller font inside all alert/info/success/warning boxes */
    [data-testid="stAlertContainer"] p,
    [data-testid="stAlertContainer"] li {
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Main Content ---
col_title, col_nav1, col_nav2 = st.columns([4, 1, 1])
with col_title:
    st.header("ICR and Token Economics")
with col_nav1:
    st.page_link("pages/payload_generator.py", label="Payload Generator", icon="🛠️")
with col_nav2:
    st.page_link("pages/help.py", label="Help & Glossary", icon="📖")

st.markdown(
    "*Same intent. Different interaction architecture. Different token economics.*"
)
st.markdown(
    "ICR Lab simulates six interaction modes and compares their token footprint:"
)
st.markdown(
    "- **Verbose Prompting** — long, detailed prompts with repeated context\\n"
    "- **Clarification Heavy** — multiple back-and-forth rounds\\n"
    "- **Context Aware** — structured requests with partial reuse\\n"
    "- **Intent Optimized** — single compressed intent expression\\n"
    "- **Over Compressed** — too terse, triggers correction loops that amplify tokens\\n"
    "- **Assumption Led** — agent infers missing context, states assumptions, and executes"
    " — correction loops emerge when assumptions are wrong"
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
_METRICS_VERSION = 10
if st.session_state.get("_metrics_version") != _METRICS_VERSION:
    for key in ["results", "metrics", "savings", "task", "operations"]:
        st.session_state.pop(key, None)
    st.session_state["_metrics_version"] = _METRICS_VERSION

if not run_clicked and "results" not in st.session_state:
    st.info("Click **Run Simulation** to compare interaction modes.")
    st.stop()

# Run simulation — triggered by button click OR assumption_accuracy slider change
# (accuracy is a simulation parameter, not a post-processing step)
_accuracy_changed = (
    "results" in st.session_state
    and "Assumption Led" in (selected_modes or [])
    and assumption_accuracy != st.session_state.get("assumption_accuracy")
)

if run_clicked or _accuracy_changed:
    operations = get_operations_count(task_input)
    with st.spinner("Running simulation…"):
        results = run_simulation(
            task_input,
            operations,
            selected_modes,
            assumption_accuracy=assumption_accuracy,
        )

    # Store uncompressed results in session state
    st.session_state["results"] = results
    st.session_state["task"] = task_input
    st.session_state["operations"] = operations
    st.session_state["assumption_accuracy"] = assumption_accuracy
    st.session_state["requirements_list"] = requirements_list
    st.session_state["run_count"] = st.session_state.get("run_count", 0) + 1

    st.toast("Simulation complete", icon="✅")

# Retrieve from session state
results = st.session_state["results"]
task = st.session_state["task"]
operations = st.session_state["operations"]
# Requirements: prefer the live sidebar value so updates without re-run still work
_stored_reqs = st.session_state.get("requirements_list", [])
active_requirements = requirements_list if requirements_list else _stored_reqs

# Apply compression reactively (slider updates without re-running simulation)
if compression_factor < 1.0:
    results = apply_output_compression(results, compression_factor)

metrics = compute_metrics(results)
savings = compute_savings(metrics)

# --- Task Context ---
st.markdown(f"**Task:** {task}")
st.markdown(
    f"**Intent Fulfilled (ICR baseline):** {operations} ops compressed into 1 intent"
)
_run_count = st.session_state.get("run_count", 1)
_last_acc = st.session_state.get("assumption_accuracy", assumption_accuracy)
st.caption(
    f"Run #{_run_count} · Assumption accuracy: {_last_acc:.0%} · "
    f"{int(_last_acc * 100)}% of assumptions correct"
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
    df = efficiency_dataframe(metrics, results)
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
    st.caption("Est. Cost based on $0.01/1K input tokens, $0.03/1K output tokens.")

# --- Prompt Comparison ---
st.divider()
st.subheader("Prompt Comparison")
st.caption("Side-by-side: how the same intent looks at different compression levels")

# Find verbose and optimized results
verbose_result = next((r for r in results if r.mode == "Verbose Prompting"), None)
optimized_result = next((r for r in results if r.mode == "Intent Optimized"), None)

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
        st.markdown("**Intent Optimized**")
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

# --- Requirements Coverage ---
if active_requirements:
    st.divider()
    st.subheader("Requirements Coverage")
    st.caption(
        "Green = covered by ops achieved · Red = missed. "
        "Lower assumption accuracy reduces ops achieved for Assumption Led."
    )
    coverage_rows = []
    for i, req_name in enumerate(active_requirements):
        row = {"Requirement": req_name}
        for r in results:
            row[r.mode] = "✅" if i < r.operations_achieved else "❌"
        coverage_rows.append(row)
    st.dataframe(pd.DataFrame(coverage_rows), hide_index=True, width="stretch")

# --- Interaction Traces ---
st.divider()
st.subheader("Interaction Traces")

for result in results:
    with st.expander(
        f"{result.mode} — {len(result.rounds)} round(s), {result.total_tokens:,} total tokens"
    ):
        for r in result.rounds:
            source_badge = "📐" if r.token_source == "measured" else "~"
            st.markdown(
                f"**Round {r.round_number}:** {r.description}  \n"
                f"↳ Input: {source_badge}{r.input_tokens:,} | Output: ~{r.output_tokens:,} | "
                f"Cumulative: {r.cumulative_tokens:,}"
            )
            if r.prompt_text:
                st.code(r.prompt_text, language=None)
            if r.assumptions:
                st.info("**Assumptions made:** " + " · ".join(r.assumptions))

        # Show optimized alternative for non-optimal modes
        if result.mode != "Intent-Optimized" and result.optimized_prompt:
            st.divider()
            st.markdown("**Intent-Optimized Alternative:**")
            st.success(result.optimized_prompt)
