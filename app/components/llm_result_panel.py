"""LLM result panel — displays live optimization output from a real backend."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def render_llm_result(is_simulation: bool) -> None:
    """Render the live LLM optimization result panel.

    Reads from st.session_state["live_optimization"] which is populated
    when a real backend (non-simulation) completes an optimization call.

    Args:
        is_simulation: Whether the current backend is the simulation engine.
    """
    if "live_optimization" in st.session_state:
        st.divider()
        st.subheader("Live LLM Result")
        live = st.session_state["live_optimization"]
        st.caption(
            f"The **{live['backend'].title()}** backend compressed your task into an "
            "intent-optimized prompt. Compare this real output against the simulated "
            '"Intent-Optimized" mode above.'
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
                    "Short tasks are often already intent-optimized \u2014 the LLM adds detail "
                    "rather than compressing. This is expected for concise inputs."
                )

        # Graphical token cost breakdown
        token_fig = go.Figure()
        token_fig.add_trace(
            go.Bar(
                x=["Input Tokens", "Output Tokens"],
                y=[live["input_tokens"], live["output_tokens"]],
                marker_color=["#636EFA", "#EF553B"],
                text=[f"{live['input_tokens']:,}", f"{live['output_tokens']:,}"],
                textposition="outside",
            )
        )
        token_fig.update_layout(
            title="LLM Token Cost for This Optimization",
            yaxis_title="Tokens",
            height=250,
            margin={"t": 40, "b": 20, "l": 40, "r": 20},
            showlegend=False,
        )
        st.plotly_chart(token_fig, width="stretch")
        st.caption(
            f"Total: {live['input_tokens'] + live['output_tokens']:,} tokens "
            f"(input: prompt + task, output: compressed result)"
        )
    elif not is_simulation:
        with st.expander("Live LLM Result", expanded=False):
            st.caption("Run with an LLM backend to see real optimization results here.")
