"""Skill opportunities panel — operations detected and skill matching."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.principles import PRINCIPLES
from metrics.ops_patterns import count_ops_by_type
from metrics.skill_matcher import match_skills, platform_supports_skills


def render_skill_panel(task_text: str, backend_name: str, is_simulation: bool) -> None:
    """Render the skill opportunities section.

    Args:
        task_text: The task description text to match against skills.
        backend_name: Active backend name (affects matching strategy).
        is_simulation: Whether the current backend is the simulation engine.
    """
    ops_by_type = count_ops_by_type(task_text)
    _skill_spinner_msg = (
        f"Matching skills with {backend_name.title()}..."
        if not is_simulation
        else "Matching skills (keyword)..."
    )
    with st.spinner(_skill_spinner_msg):
        skill_matches = match_skills(task_text, backend_name=backend_name)
    has_skills = platform_supports_skills(backend_name)

    if not ops_by_type and not skill_matches:
        return

    expand_skills = not is_simulation and (bool(skill_matches) or bool(ops_by_type))
    with st.expander("Skill Opportunities", expanded=expand_skills):
        if ops_by_type:
            # Horizontal bar chart of operations by category
            categories = list(ops_by_type.keys())
            counts = list(ops_by_type.values())
            ops_fig = go.Figure(
                go.Bar(
                    x=counts,
                    y=categories,
                    orientation="h",
                    marker_color="#636EFA",
                    text=counts,
                    textposition="outside",
                )
            )
            ops_fig.update_layout(
                title=f"Operations Detected ({sum(counts)} total)",
                xaxis_title="Count",
                height=max(150, len(categories) * 40 + 80),
                margin={"t": 40, "b": 20, "l": 120, "r": 20},
                showlegend=False,
            )
            st.plotly_chart(ops_fig, width="stretch")

        if skill_matches:
            st.markdown("**Matching Skills:**")
            for s in skill_matches:
                avail_icon = (
                    "🟢" if s.get("available") else "🔵" if s.get("available") is None else "🔴"
                )
                st.markdown(
                    f"- {avail_icon} `{s['skill']}` — "
                    f"ICR {s['icr_estimate']} "
                    f"({s['match_count']}/{s['total_patterns']} patterns matched)"
                )
            st.caption(f"*{PRINCIPLES['skills']}*")

            # Show platform skill support info
            if not has_skills:
                st.info(
                    f"**{backend_name.title()}** does not support reusable skills. "
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
