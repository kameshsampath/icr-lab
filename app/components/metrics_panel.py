"""Metrics panel component — top-level ICR scores, amplification, and compression callouts.

Renders the summary metrics row and contextual insight callouts.
"""

from __future__ import annotations

import streamlit as st

from app.principles import PRINCIPLES
from metrics.calculator import ModeMetrics
from visuals.charts import icr_gauge_chart


def render_metrics(
    metrics: list[ModeMetrics],
    savings: dict,
    compression_factor: float,
    is_simulation: bool,
) -> None:
    """Render top-level metrics and insight callouts.

    Args:
        metrics: Computed ModeMetrics list from compute_metrics().
        savings: Summary dict from compute_savings().
        compression_factor: Current compression factor (1.0 = none).
        is_simulation: Whether running in simulation mode.
    """
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
            help=(
                "Estimated cost reduction (hypothetical rates for comparison"
                " — not actual provider pricing)"
            ),
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
        r"\quad \Rightarrow \quad 1.0 = \text{most efficient},"
        r"\ 0.5 = 2\times\text{ more tokens per op}"
    )
    st.write("")
    st.plotly_chart(icr_gauge_chart(metrics), width="stretch")
