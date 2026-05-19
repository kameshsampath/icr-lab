"""Home — ICR and Token Economics dashboard."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backends import get_backend, list_backends
from backends.config import _get_snowflake_connection_info
from examples.sample_tasks import SAMPLE_TASKS, VERBOSE_TASKS, get_operations_count
from metrics.calculator import compute_metrics, compute_savings
from metrics.ops_patterns import count_ops_by_type
from metrics.skill_matcher import match_skills, platform_supports_skills
from simulations.engine import SIMULATION_MODES, run_simulation, apply_output_compression
from visuals.charts import (
    cumulative_growth_chart,
    efficiency_dataframe,
    icr_gauge_chart,
    token_comparison_chart,
)
from app.principles import PRINCIPLES, TOKEN_ECONOMICS_URL

# --- Sidebar controls ---
with st.sidebar:
    st.title("ICR Lab")
    st.caption("Intent Compression Ratio & Token Economics")

    st.divider()

    # Backend selection (first, so it influences task ordering)
    st.markdown("**Backend**")
    available_backends = list_backends()

    # Cached connection check (avoids re-testing on every widget interaction)
    @st.cache_data(ttl=300, show_spinner=False)
    def _check_cortex_connection() -> tuple[bool, str]:
        """Check cortex availability, cached for 5 minutes."""
        try:
            backend_instance = get_backend("cortex")
            if backend_instance.is_available():
                return True, ""
            return False, "Snowflake connection failed"
        except Exception as e:
            return False, str(e)

    # Check cortex availability with spinner
    cortex_available = True
    cortex_reason = ""
    cortex_configured = any(name == "cortex" for name, _, _ in available_backends)
    if cortex_configured:
        with st.spinner("Checking Snowflake connection..."):
            cortex_available, cortex_reason = _check_cortex_connection()

    backend_options = []
    backend_help = {}
    for name, usable, reason in available_backends:
        display_name = name.title()  # Init Caps: "simulation" -> "Simulation", "cortex" -> "Cortex"
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
    # Determine if selected backend is usable
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

    # Example task selection (reordered based on backend)
    _SNOWFLAKE_KEYWORDS = {"snowflake", "cortex", "snowpark", "iceberg", "openflow", "native app", "dynamic tables"}

    def _is_snowflake_task(task: str) -> bool:
        task_lower = task.lower()
        return any(kw in task_lower for kw in _SNOWFLAKE_KEYWORDS)

    if selected_backend_name == "cortex":
        # Snowflake tasks first when Cortex is selected
        sf_tasks = [t for t in SAMPLE_TASKS if _is_snowflake_task(t)]
        other_tasks = [t for t in SAMPLE_TASKS if not _is_snowflake_task(t)]
        ordered_tasks = sf_tasks + other_tasks
    else:
        ordered_tasks = SAMPLE_TASKS

    # Build dropdown: (custom) + short tasks + verbose tasks
    verbose_labels = [v["label"] for v in VERBOSE_TASKS]
    all_options = ["(custom)"] + ordered_tasks + verbose_labels

    example_choice = st.selectbox(
        "Example Tasks",
        options=all_options,
        index=0,
        help="Short tasks show interaction architecture differences. "
        "[Verbose] tasks demonstrate real LLM compression value.",
    )

    # Resolve task text from selection
    verbose_map = {v["label"]: v["text"] for v in VERBOSE_TASKS}

    if example_choice == "(custom)":
        task_input = st.text_area(
            "Task Description",
            placeholder="e.g., Deploy payment service with autoscaling and observability",
            height=100,
        )
    elif example_choice in verbose_map:
        task_input = st.text_area(
            "Task Description",
            value=verbose_map[example_choice],
            height=200,
        )
    else:
        task_input = st.text_area(
            "Task Description",
            value=example_choice,
            height=100,
        )

    # File upload for custom task text/markdown
    uploaded_file = st.file_uploader(
        "Or upload a task file",
        type=["txt", "md"],
        help="Upload a .txt or .md file with a verbose task description for compression analysis.",
    )
    if uploaded_file is not None:
        task_input = uploaded_file.read().decode("utf-8")

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

    # Single dynamic action button (always at bottom)
    is_simulation = selected_backend_name == "simulation"
    button_label = "Run Simulation" if is_simulation else "Optimize with AI"
    run_clicked = st.button(
        button_label,
        type="primary",
        width="stretch",
        disabled=not task_input or not selected_modes or (not is_simulation and not backend_usable),
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
st.markdown(f"**Task:** {task}")
st.markdown(
    f"**Intent Fulfilled (ICR baseline):** {operations} ops compressed into 1 intent"
)
if not is_simulation:
    st.caption(
        "Token values below are **simulated** (deterministic engine). "
        "Scroll to \"Live LLM Result\" for the actual LLM output."
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
        help="Estimated cost reduction (hypothetical rates for comparison — not actual provider pricing)",
    )

# --- Amplification callout ---
worst_mode = max(metrics, key=lambda m: m.token_amplification)
if worst_mode.token_amplification > 1.0:
    st.info(
        f"**{worst_mode.mode}** uses **{worst_mode.token_amplification:.1f}x** more tokens "
        f"than the most efficient mode for the same intent."
    )
    st.caption(f"*{PRINCIPLES['amplification']}*")

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

# --- Live Optimization Result ---
if "live_optimization" in st.session_state:
    st.divider()
    st.subheader("Live LLM Result")
    live = st.session_state["live_optimization"]
    st.caption(
        f"The **{live['backend'].title()}** backend compressed your task into an "
        "intent-optimized prompt. Compare this real output against the simulated "
        "\"Intent-Optimized\" mode above."
    )

    col_orig, col_opt = st.columns(2)
    with col_orig:
        st.markdown("**Original Task**")
        st.error(live["original"])
        st.caption(f"~{len(live['original'].split())} words")

    with col_opt:
        st.markdown("**AI-Optimized**")
        st.success(live["optimized"])
        st.caption(f"~{len(live['optimized'].split())} words")

    orig_words = len(live["original"].split())
    opt_words = len(live["optimized"].split())
    if orig_words > 0:
        reduction = round((1 - opt_words / orig_words) * 100)
        if reduction > 0:
            st.metric("Word Reduction", f"{reduction}%")
        else:
            st.warning(
                f"The LLM output is **{abs(reduction)}% longer** than the original. "
                "Short tasks are often already intent-optimized — the LLM adds detail "
                "rather than compressing. This is expected for concise inputs."
            )

    # Graphical token cost breakdown
    import plotly.graph_objects as go
    token_fig = go.Figure()
    token_fig.add_trace(go.Bar(
        x=["Input Tokens", "Output Tokens"],
        y=[live["input_tokens"], live["output_tokens"]],
        marker_color=["#636EFA", "#EF553B"],
        text=[f"{live['input_tokens']:,}", f"{live['output_tokens']:,}"],
        textposition="outside",
    ))
    token_fig.update_layout(
        title="LLM Token Cost for This Optimization",
        yaxis_title="Tokens",
        height=250,
        margin=dict(t=40, b=20, l=40, r=20),
        showlegend=False,
    )
    st.plotly_chart(token_fig, use_container_width=True)
    st.caption(
        f"Total: {live['input_tokens'] + live['output_tokens']:,} tokens "
        f"(input: prompt + task, output: compressed result)"
    )
elif not is_simulation:
    with st.expander("Live LLM Result", expanded=False):
        st.caption("Run with an LLM backend to see real optimization results here.")

# --- Skill Opportunities ---
import plotly.graph_objects as go

ops_by_type = count_ops_by_type(task)
skill_matches = match_skills(task)
has_skills = platform_supports_skills(selected_backend_name)

if ops_by_type or skill_matches:
    expand_skills = not is_simulation and (bool(skill_matches) or bool(ops_by_type))
    with st.expander("Skill Opportunities", expanded=expand_skills):
        if ops_by_type:
            # Horizontal bar chart of operations by category
            categories = list(ops_by_type.keys())
            counts = list(ops_by_type.values())
            ops_fig = go.Figure(go.Bar(
                x=counts,
                y=categories,
                orientation="h",
                marker_color="#636EFA",
                text=counts,
                textposition="outside",
            ))
            ops_fig.update_layout(
                title=f"Operations Detected ({sum(counts)} total)",
                xaxis_title="Count",
                height=max(150, len(categories) * 40 + 80),
                margin=dict(t=40, b=20, l=120, r=20),
                showlegend=False,
            )
            st.plotly_chart(ops_fig, use_container_width=True)

        if skill_matches:
            st.markdown("**Matching Skills:**")
            for s in skill_matches:
                avail_icon = "🟢" if s.get("available") else "🔵" if s.get("available") is None else "🔴"
                st.markdown(
                    f"- {avail_icon} `{s['skill']}` — "
                    f"ICR {s['icr_estimate']} "
                    f"({s['match_count']}/{s['total_patterns']} patterns matched)"
                )
            st.caption(f"*{PRINCIPLES['skills']}*")

            # Show platform skill support info
            if not has_skills:
                st.info(
                    f"**{selected_backend_name.title()}** does not support reusable skills. "
                    "Platforms with skill support: Cortex Code, Claude, Codex, Gemini. "
                    "Skills eliminate repeated context by packaging operational knowledge "
                    "into reusable intent patterns."
                )
        elif ops_by_type:
            st.caption(
                "No skill patterns matched this task, but the operations above "
                "could become a custom skill to reduce repetition."
            )
            st.caption(f"*{PRINCIPLES['repetition_tax']}*")

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
    st.caption(
        "⚠️ Est. Cost uses hypothetical rates ($0.01/1K input, $0.03/1K output) "
        "for relative comparison only. Actual costs vary by provider and model — "
        "check your LLM backend's pricing for real numbers."
    )

# --- Prompt Comparison ---
st.divider()
with st.expander("Prompt Comparison", expanded=False):
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

    st.caption(f"*{PRINCIPLES['intent_optimization']}*")

# --- Interaction Traces ---
st.divider()
with st.expander("Interaction Traces", expanded=False):
    for result in results:
        with st.container():
            st.markdown(
                f"**{result.mode}** — {len(result.rounds)} round(s), "
                f"{result.total_tokens:,} total tokens"
            )
            for r in result.rounds:
                st.markdown(
                    f"Round {r.round_number}: {r.description}  \n"
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
            st.divider()

# --- Article link ---
st.divider()
st.markdown(
    f"[Read the full article: ICR and Token Economics]({TOKEN_ECONOMICS_URL})"
)
st.caption(
    "ICR Lab is a companion demo for the article. "
    "It makes token economics visible so the principles are easier to apply."
)

