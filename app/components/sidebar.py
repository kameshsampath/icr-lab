"""Sidebar component — backend selection, task picker, modes, compression, actions.

Renders the full sidebar UI and returns a SidebarState dataclass with
all user selections for the main page to consume.
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from backends import list_backends
from backends.config import _get_snowflake_connection_info
from examples.sample_tasks import SAMPLE_TASKS, VERBOSE_TASKS
from simulations.engine import SIMULATION_MODES

_SNOWFLAKE_KEYWORDS = {
    "snowflake",
    "cortex",
    "snowpark",
    "iceberg",
    "openflow",
    "native app",
    "dynamic tables",
}


@dataclass
class SidebarState:
    """All user selections from the sidebar."""

    backend_name: str
    backend_usable: bool
    task_text: str
    selected_modes: list[str]
    compression_factor: float
    run_clicked: bool
    refresh_clicked: bool
    is_simulation: bool


def _is_snowflake_task(task: str) -> bool:
    task_lower = task.lower()
    return any(kw in task_lower for kw in _SNOWFLAKE_KEYWORDS)


@st.cache_data(ttl=300, show_spinner=False)
def _check_cortex_connection() -> tuple[bool, str]:
    """Check cortex availability, cached for 5 minutes."""
    from backends import get_backend  # noqa: PLC0415

    try:
        backend_instance = get_backend("cortex")
        if backend_instance.is_available():
            return True, ""
        return False, "Snowflake connection failed"
    except Exception as e:
        return False, str(e)


def render_sidebar() -> SidebarState:  # noqa: PLR0912, PLR0915
    """Render the full sidebar and return user selections."""
    with st.sidebar:
        st.title("ICR Lab")
        st.caption("Intent Compression Ratio & Token Economics")

        st.divider()

        # --- Refresh button ---
        refresh_clicked = st.button("🔄 Refresh", help="Clear cached data and refresh")
        if refresh_clicked:
            st.cache_data.clear()

        # --- Backend selection ---
        st.markdown("**Backend**")
        available_backends = list_backends()

        # Check cortex availability with spinner
        cortex_available = True
        cortex_reason = ""
        cortex_configured = any(name == "cortex" for name, _, _ in available_backends)
        if cortex_configured:
            with st.spinner("Checking Snowflake connection..."):
                cortex_available, cortex_reason = _check_cortex_connection()

        backend_options = []
        backend_help: dict[str, str] = {}
        for name, usable, reason in available_backends:
            display_name = name.title()
            if name == "cortex" and not cortex_available:
                label = f"🔴 {display_name} (unavailable)"
                backend_options.append(label)
                backend_help[label] = cortex_reason
            elif not usable:
                label = f"🔴 {display_name} (unavailable)"
                backend_options.append(label)
                backend_help[label] = reason
            else:
                label = f"🟢 {display_name}"
                backend_options.append(label)
                backend_help[label] = ""

        selected_backend = st.radio(
            "Select Backend",
            options=backend_options,
            index=0,
            label_visibility="collapsed",
            help="Select a backend. 🟢 = connected, 🔴 = unavailable.",
        )
        # Strip the dot indicator and "(unavailable)" to get the raw name
        selected_backend_name = selected_backend.lstrip("🟢🔴 ").split(" (")[0].lower()
        backend_usable = "🔴" not in selected_backend

        # Explain what the backend does
        if selected_backend_name == "simulation":
            st.caption(
                "Deterministic engine — generates synthetic token traces across 5 "
                "interaction styles. No LLM calls, no cost, instant results."
            )
        else:
            st.caption(
                f"Calls **{selected_backend_name.title()}** to generate a real optimized prompt "
                "from your task, then runs the simulation to compare all interaction "
                "styles. You'll see both the simulated breakdown and the live LLM result."
            )

        # Snowflake connection info (collapsible)
        if cortex_configured:
            with st.expander("Snowflake Connection", expanded=False):
                conn_info = _get_snowflake_connection_info()
                if cortex_available:
                    st.success("Connected", icon="✅")
                else:
                    st.error("Connection failed", icon="❌")
                st.markdown(f"**Connection:** {conn_info['connection']}")
                st.markdown(f"**User:** {conn_info['user']}")
                if conn_info["warehouse"]:
                    st.markdown(f"**Warehouse:** {conn_info['warehouse']}")
                if conn_info["role"]:
                    st.markdown(f"**Role:** {conn_info['role']}")

        st.divider()

        # --- Example task selection ---
        if selected_backend_name == "cortex":
            sf_tasks = [t for t in SAMPLE_TASKS if _is_snowflake_task(t)]
            other_tasks = [t for t in SAMPLE_TASKS if not _is_snowflake_task(t)]
            ordered_tasks = sf_tasks + other_tasks
        else:
            ordered_tasks = SAMPLE_TASKS

        # Build dropdown: (custom) + short tasks + verbose tasks
        verbose_labels = [v["label"] for v in VERBOSE_TASKS]
        all_options = ["(custom)", *ordered_tasks, *verbose_labels]

        example_choice = st.selectbox(
            "Example Intent Optimized Tasks",
            options=all_options,
            index=0,
            help="Short tasks show interaction architecture differences. "
            "[Verbose] tasks demonstrate real LLM compression value.",
        )

        # Resolve task text from selection
        verbose_map = {v["label"]: v["text"] for v in VERBOSE_TASKS}

        if example_choice == "(custom)":
            task_input = ""
        elif example_choice in verbose_map:
            task_input = verbose_map[example_choice]
        else:
            task_input = example_choice

        # Custom task text input
        custom_task = st.text_area(
            "Or enter your own task",
            value="" if example_choice != "(custom)" else "",
            placeholder="Describe your task here...",
            height=100,
            help="Type a custom task description. This overrides the dropdown selection.",
        )
        if custom_task.strip():
            task_input = custom_task.strip()

        # File upload for custom task text/markdown
        uploaded_file = st.file_uploader(
            "Or upload a task file",
            type=["txt", "md"],
            help=(
                "Upload a .txt or .md file with a verbose task description"
                " for compression analysis."
            ),
        )
        if uploaded_file is not None:
            task_input = uploaded_file.read().decode("utf-8")

        st.divider()

        # --- Mode selection ---
        selected_modes = st.multiselect(
            "Simulation Modes",
            options=list(SIMULATION_MODES.keys()),
            default=list(SIMULATION_MODES.keys()),
            help="Select which interaction modes to compare",
        )

        st.divider()

        # Determine mode early (needed for conditional UI below)
        is_simulation = selected_backend_name == "simulation"

        # --- Output compression toggle (simulation only) ---
        compression_factor = 1.0
        if is_simulation:
            st.markdown("**Output Compression**")
            apply_compression = st.toggle(
                "Caveman-style compression",
                value=False,
                help="Simulates terse AI responses (~35% output token reduction). "
                "Shows how output brevity interacts with interaction architecture.",
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

        st.divider()

        # --- Single dynamic action button ---
        button_label = "Run Simulation" if is_simulation else "Optimize with AI"
        _btn_disabled = (
            not task_input or not selected_modes or (not is_simulation and not backend_usable)
        )
        run_clicked = st.button(
            button_label,
            type="primary",
            width="stretch",
            disabled=_btn_disabled,
        )

    return SidebarState(
        backend_name=selected_backend_name,
        backend_usable=backend_usable,
        task_text=task_input,
        selected_modes=selected_modes,
        compression_factor=compression_factor,
        run_clicked=run_clicked,
        refresh_clicked=refresh_clicked,
        is_simulation=is_simulation,
    )
