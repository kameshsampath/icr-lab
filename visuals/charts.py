"""Visualization charts for ICR Lab.

Plotly-based charts for comparing token usage, growth patterns,
and efficiency across interaction modes.
"""

import plotly.graph_objects as go
import pandas as pd

from metrics.calculator import ModeMetrics
from simulations.engine import SimulationResult


# Color palette for modes (rgb tuples for easy alpha manipulation)
MODE_COLORS = {
    "Verbose Prompting": "rgb(239, 68, 68)",       # red
    "Clarification Heavy": "rgb(249, 115, 22)",    # orange
    "Context-Aware": "rgb(59, 130, 246)",           # blue
    "Intent-Optimized": "rgb(16, 185, 129)",        # green
}


def _with_alpha(rgb: str, alpha: float) -> str:
    """Convert 'rgb(r, g, b)' to 'rgba(r, g, b, alpha)'."""
    return rgb.replace("rgb(", "rgba(").replace(")", f", {alpha})")


def token_comparison_chart(metrics: list[ModeMetrics]) -> go.Figure:
    """Bar chart comparing token usage across modes.

    Grouped bars showing input and output tokens per mode.
    """
    modes = [m.mode for m in metrics]
    input_tokens = [m.total_input_tokens for m in metrics]
    output_tokens = [m.total_output_tokens for m in metrics]
    colors = [MODE_COLORS.get(m, "rgb(107, 114, 128)") for m in modes]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Input Tokens",
        x=modes,
        y=input_tokens,
        marker_color=[_with_alpha(c, 0.85) for c in colors],
        text=[f"{t:,}" for t in input_tokens],
        textposition="auto",
    ))

    fig.add_trace(go.Bar(
        name="Output Tokens",
        x=modes,
        y=output_tokens,
        marker_color=[_with_alpha(c, 0.5) for c in colors],
        text=[f"{t:,}" for t in output_tokens],
        textposition="auto",
    ))

    fig.update_layout(
        title="Token Usage by Interaction Mode",
        xaxis_title="Mode",
        yaxis_title="Tokens",
        barmode="group",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=60),
    )

    return fig


def cumulative_growth_chart(results: list[SimulationResult]) -> go.Figure:
    """Line chart showing cumulative token growth across interaction rounds."""
    fig = go.Figure()

    for result in results:
        rounds = [r.round_number for r in result.rounds]
        cumulative = [r.cumulative_tokens for r in result.rounds]
        color = MODE_COLORS.get(result.mode, "rgb(107, 114, 128)")

        # Add starting point at 0
        rounds = [0] + rounds
        cumulative = [0] + cumulative

        fig.add_trace(go.Scatter(
            x=rounds,
            y=cumulative,
            mode="lines+markers",
            name=result.mode,
            line=dict(color=color, width=3),
            marker=dict(size=8),
            hovertemplate="%{y:,} tokens at round %{x}<extra>%{fullData.name}</extra>",
        ))

    fig.update_layout(
        title="Cumulative Token Growth",
        xaxis_title="Interaction Round",
        yaxis_title="Cumulative Tokens",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=60),
    )

    fig.update_xaxes(dtick=1)

    return fig


def efficiency_dataframe(metrics: list[ModeMetrics]) -> pd.DataFrame:
    """Create a styled comparison table of efficiency metrics."""
    data = {
        "Mode": [m.mode for m in metrics],
        "Rounds": [m.interaction_rounds for m in metrics],
        "Input Tokens": [f"{m.total_input_tokens:,}" for m in metrics],
        "Output Tokens": [f"{m.total_output_tokens:,}" for m in metrics],
        "Total Tokens": [f"{m.total_tokens:,}" for m in metrics],
        "Est. Cost": [f"${m.estimated_cost:.4f}" for m in metrics],
        "ICR Score": [round(m.icr_score * 100, 1) for m in metrics],
        "Amplification": [f"{m.token_amplification:.1f}x" for m in metrics],
    }

    return pd.DataFrame(data)


def icr_gauge_chart(metrics: list[ModeMetrics]) -> go.Figure:
    """Small multiples of ICR scores as indicator gauges."""
    from plotly.subplots import make_subplots

    n = len(metrics)
    fig = make_subplots(
        rows=1, cols=n,
        specs=[[{"type": "indicator"}] * n],
        horizontal_spacing=0.05,
    )

    for i, m in enumerate(metrics):
        color = MODE_COLORS.get(m.mode, "rgb(107, 114, 128)")
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=m.icr_score * 100,
            title={"text": m.mode, "font": {"size": 12}},
            number={"font": {"size": 20}, "suffix": "%"},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=color),
                bgcolor="white",
                steps=[
                    dict(range=[0, 30], color="rgb(254, 226, 226)"),
                    dict(range=[30, 60], color="rgb(254, 243, 199)"),
                    dict(range=[60, 100], color="rgb(209, 250, 229)"),
                ],
            ),
        ), row=1, col=i + 1)

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white",
    )

    return fig
