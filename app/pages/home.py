"""Home — ICR and Token Economics dashboard."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.components.charts_panel import render_charts  # noqa: E402
from app.components.llm_result_panel import render_llm_result  # noqa: E402
from app.components.metrics_panel import render_metrics  # noqa: E402
from app.components.sidebar import SidebarState, render_sidebar  # noqa: E402
from app.components.skill_panel import render_skill_panel  # noqa: E402
from backends import get_backend  # noqa: E402
from examples.sample_tasks import get_operations_count  # noqa: E402
from metrics.calculator import compute_metrics, compute_savings  # noqa: E402
from simulations.engine import apply_output_compression, run_simulation  # noqa: E402

# --- Sidebar ---
state: SidebarState = render_sidebar()

# --- Main Content ---
col_title, col_nav = st.columns([4, 1])
with col_title:
    st.header("ICR and Token Economics")
with col_nav:
    st.page_link("pages/help.py", label="Help & Glossary", icon="📖")

st.markdown("*Same intent. Different interaction architecture. Different token economics.*")
st.markdown("ICR Lab simulates five interaction modes and compares their token footprint:")
st.markdown(
    "- **Verbose Prompting** — long, detailed prompts with repeated context\n"
    "- **Clarification Heavy** — multiple back-and-forth rounds\n"
    "- **Context-Aware** — structured requests with partial reuse\n"
    "- **Intent-Optimized** — single compressed intent expression\n"
    "- **Over-Compressed** — too terse, triggers correction loops that amplify tokens"
)

# ICR Formula
with st.expander("📐 ICR Formula", expanded=True):
    st.latex(r"\text{ICR} = \frac{\text{Intent Fulfilled}}{\text{Total Tokens}} \times 1000")
    st.caption("Higher ICR = more useful work completed per token consumed.")

# --- Task Description (main area for readability) ---
_height = 200 if len(state.task_text) > 200 else 100

st.markdown("### Task Description")
task_input = st.text_area(
    "",
    value=state.task_text,
    height=_height,
    placeholder="e.g., Deploy payment service with autoscaling and observability",
    disabled=True,
    help="Selected from the sidebar. Shows the full task text for readability.",
)

if not task_input:
    st.info("Select a task from the sidebar and click **Run Simulation** to begin.")
    st.stop()

# Aliases for readability
selected_backend_name = state.backend_name
is_simulation = state.is_simulation
backend_usable = state.backend_usable
compression_factor = state.compression_factor
selected_modes = state.selected_modes
run_clicked = state.run_clicked

# --- Reset session state when task changes ---
if task_input != st.session_state.get("_last_task_input"):
    for key in ["results", "metrics", "savings", "task", "operations", "live_optimization"]:
        st.session_state.pop(key, None)
    st.session_state["_last_task_input"] = task_input

if not run_clicked and "results" not in st.session_state:
    action_hint = "Run Simulation" if is_simulation else "Optimize with AI"
    st.info(f"Click **{action_hint}** to compare interaction modes.")
    st.stop()

# Handle live optimization (non-simulation backend)
if run_clicked and not is_simulation and backend_usable:
    with st.spinner(f"Optimizing with {selected_backend_name}..."):
        try:
            backend = get_backend(selected_backend_name)
            optimize_prompt = (
                "You are an intent compression expert. Your job is to rewrite the task below "
                "into the shortest possible prompt that preserves ALL operations and requirements "
                "but eliminates redundancy, filler words, and verbose explanation.\n\n"
                "Rules:\n"
                "- Output ONLY the compressed prompt, nothing else\n"
                "- Preserve every distinct operation/requirement\n"
                "- Use terse, structured language (imperative verbs, no articles where possible)\n"
                "- Use semicolons or bullet notation to separate operations\n"
                "- If the input is already short (<20 words), return it unchanged\n\n"
                f"TASK TO COMPRESS:\n{task_input}"
            )
            result = backend.complete(optimize_prompt)
            st.session_state["live_optimization"] = {
                "original": task_input,
                "optimized": result.text,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "backend": selected_backend_name,
            }
        except Exception as e:
            st.error(f"Backend error: {e}")

# Run simulation (always runs when button is clicked)
if run_clicked:
    with st.spinner("Running simulation..."):
        operations = get_operations_count(task_input)
        results = run_simulation(task_input, operations, selected_modes)

    # Store uncompressed results in session state
    st.session_state["results"] = results
    st.session_state["task"] = task_input
    st.session_state["operations"] = operations

# Retrieve from session state
results = st.session_state["results"]
task = st.session_state["task"]
operations = st.session_state["operations"]

# Apply compression reactively (slider updates without re-running simulation)
if compression_factor < 1.0:
    results = apply_output_compression(results, compression_factor)

metrics = compute_metrics(results)
savings = compute_savings(metrics)

# --- Task Context ---
st.markdown(f"**Intent Fulfilled (ICR baseline):** {operations} ops compressed into 1 intent")
if not is_simulation:
    st.caption(
        "Token values below are **simulated** (deterministic engine). "
        'Scroll to "Live LLM Result" for the actual LLM output.'
    )

st.divider()

# --- Panels ---
render_metrics(metrics, savings, compression_factor, is_simulation)
render_llm_result(is_simulation)
render_skill_panel(task, selected_backend_name, is_simulation)
render_charts(results, metrics, savings)
