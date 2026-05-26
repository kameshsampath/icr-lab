"""Payload Generator — build a /simulate API request payload interactively."""

import json
import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from examples.sample_tasks import SAMPLE_TASKS  # noqa: E402
from simulations.engine import SIMULATION_MODES  # noqa: E402

# --- Header ---
col_title, col_nav = st.columns([4, 1])
with col_title:
    st.header("Payload Generator")
with col_nav:
    st.page_link("pages/home.py", label="Home", icon="🏠")

st.markdown(
    "Build a `/simulate` API request payload interactively. "
    "Adjust the controls below and copy the generated JSON or cURL command."
)
st.divider()

# --- Controls ---
st.subheader("Task")
example_choice = st.selectbox(
    "Example Tasks",
    options=["(custom)"] + sorted(SAMPLE_TASKS),
    index=0,
    help="Pick a pre-built task or write your own below",
)
if example_choice == "(custom)":
    task_value = st.text_area(
        "Task description",
        placeholder="e.g., Deploy payment service with autoscaling and observability",
        height=80,
    )
else:
    task_value = st.text_area("Task description", value=example_choice, height=80)

st.divider()

st.subheader("Operations")
use_auto_ops = st.checkbox(
    "Auto-derive from catalog (omit `operations` field)",
    value=True,
    help="When checked, the API will look up the operation count from the built-in catalog.",
)
if not use_auto_ops:
    operations_value = st.number_input(
        "Operations", min_value=1, max_value=100, value=4
    )
else:
    operations_value = None

st.divider()

st.subheader("Simulation Modes")
all_modes = sorted(SIMULATION_MODES.keys())
selected_modes = st.multiselect(
    "Modes to simulate",
    options=all_modes,
    default=all_modes,
    help="Leave empty to simulate all modes",
)

st.divider()

st.subheader("Requirements")
requirements_text = st.text_area(
    "One requirement per line (optional)",
    placeholder="input form\nweighted formula\ncolor badge\nformula breakdown",
    height=100,
    help="Requirements to map against operations_achieved. Used to compute requirements_coverage.",
)
requirements_list = [r.strip() for r in requirements_text.splitlines() if r.strip()]

st.divider()

st.subheader("Assumption Accuracy")
assumption_accuracy = st.slider(
    "Model accuracy on assumptions",
    min_value=0.0,
    max_value=1.0,
    value=1.0,
    step=0.05,
    help=(
        "Only affects Assumption Led mode. "
        "1.0 = perfect (0 wrong), 0.0 = all wrong. "
        "0.85 ≈ strong model, 0.60 ≈ mid-tier, 0.30 ≈ weak model."
    ),
)

_ACCURACY_PRESETS = {
    "Perfect (1.0)": 1.0,
    "Strong model — GPT-4 / Claude 3.5 (0.85)": 0.85,
    "Mid-tier (0.60)": 0.60,
    "Weak model (0.30)": 0.30,
    "All wrong (0.0)": 0.0,
}
preset = st.selectbox(
    "Or pick a preset",
    options=["— custom —"] + list(_ACCURACY_PRESETS.keys()),
    index=0,
)
if preset != "— custom —":
    assumption_accuracy = _ACCURACY_PRESETS[preset]
    st.caption(f"Preset applied: `assumption_accuracy = {assumption_accuracy}`")

st.divider()

with st.expander("Per-mode Operations Override (advanced)", expanded=False):
    st.caption(
        "Override how many operations each mode achieves. "
        "Useful for demoing partial coverage scenarios."
    )
    mode_ops_override: dict[str, int] = {}
    for mode in selected_modes or all_modes:
        val = st.number_input(
            mode,
            min_value=0,
            max_value=100,
            value=-1,
            step=1,
            key=f"mode_ops_{mode}",
            help="-1 = use simulated value (no override)",
        )
        if val >= 0:
            mode_ops_override[mode] = val

# --- Build payload ---
payload: dict = {"task": task_value or ""}
if operations_value is not None:
    payload["operations"] = operations_value
if selected_modes and set(selected_modes) != set(all_modes):
    payload["modes"] = selected_modes
if requirements_list:
    payload["requirements"] = requirements_list
if assumption_accuracy != 1.0:
    payload["assumption_accuracy"] = round(assumption_accuracy, 4)
if mode_ops_override:
    payload["mode_operations_achieved"] = mode_ops_override

st.divider()
st.subheader("Generated Payload")

payload_json = json.dumps(payload, indent=2)
st.code(payload_json, language="json")

# --- cURL command ---
st.subheader("cURL Command")
st.caption("Bash / zsh — copy and paste directly into your terminal.")

_compact_json = json.dumps(payload, separators=(",", ":"))
# Escape single quotes for POSIX shell: replace ' with '\''
_safe_json = _compact_json.replace("'", "'\\''")
curl_cmd = (
    "curl -s -X POST http://localhost:8000/simulate \\\n"
    "  -H 'Content-Type: application/json' \\\n"
    f"  -d '{_safe_json}'"
)
st.code(curl_cmd, language="bash")
st.caption(
    "Point at the live app API by replacing `localhost:8000` with your deployment URL. "
    "This command uses POSIX single-quote escaping and is safe for bash/zsh. "
    "On Windows use `cmd` with double-quote escaping instead."
)

st.divider()
st.page_link("pages/help.py", label="Help & Glossary", icon="📖")
