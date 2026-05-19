"""Charts panel — token comparison, cumulative growth, efficiency table, and traces."""

from __future__ import annotations

import streamlit as st

from app.principles import PRINCIPLES, TOKEN_ECONOMICS_URL
from metrics.calculator import ModeMetrics
from simulations.engine import SimulationResult
from visuals.charts import (
    cumulative_growth_chart,
    efficiency_dataframe,
    token_comparison_chart,
)


def render_charts(  # noqa: PLR0915
    results: list[SimulationResult],
    metrics: list[ModeMetrics],
    savings: dict,
) -> None:
    """Render token comparison charts, efficiency table, prompt comparison, and traces.

    Args:
        results: Simulation results for each mode.
        metrics: Computed ModeMetrics for each mode.
        savings: Savings dict from compute_savings().
    """
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
            "\u26a0\ufe0f Est. Cost uses hypothetical rates ($0.01/1K input, $0.03/1K output) "
            "for relative comparison only. Actual costs vary by provider and model \u2014 "
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
                reduction = round((1 - len(opt_prompt.split()) / len(verbose_prompt.split())) * 100)
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
                    f"**{result.mode}** \u2014 {len(result.rounds)} round(s), "
                    f"{result.total_tokens:,} total tokens"
                )
                for r in result.rounds:
                    st.markdown(
                        f"Round {r.round_number}: {r.description}  \n"
                        f"\u21b3 Input: {r.input_tokens:,} | Output: {r.output_tokens:,} | "
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
    st.markdown(f"[Read the full article: ICR and Token Economics]({TOKEN_ECONOMICS_URL})")
    st.caption(
        "ICR Lab is a companion demo for the article. "
        "It makes token economics visible so the principles are easier to apply."
    )
