"""Metrics calculator for ICR Lab.

Computes Intent Compression Ratio, token amplification factor,
and estimated costs from simulation results.
"""

from dataclasses import dataclass

from simulations.engine import SimulationResult

# Approximate pricing (per 1K tokens)
INPUT_COST_PER_1K = 0.01  # $0.01 per 1K input tokens
OUTPUT_COST_PER_1K = 0.03  # $0.03 per 1K output tokens


@dataclass
class ModeMetrics:
    """Computed metrics for a single simulation mode."""

    mode: str
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    interaction_rounds: int
    estimated_cost: float
    icr_score: float  # normalized 0-1, highest = 1.0
    token_amplification: float


def compute_cost(input_tokens: int, output_tokens: int) -> float:
    """Compute estimated cost from token counts."""
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K
    return round(input_cost + output_cost, 4)


def compute_icr(operations: int, total_tokens: int) -> float:
    """Compute raw Intent Compression Ratio.

    ICR = (Operations Achieved / Total Tokens) * 1000

    Higher ICR means more operations achieved per token spent.
    Returns the raw value; normalization to 0-1 happens in compute_metrics.
    """
    if total_tokens == 0:
        return 0.0
    return (operations / total_tokens) * 1000


def compute_metrics(results: list[SimulationResult]) -> list[ModeMetrics]:
    """Compute metrics for all simulation results.

    ICR scores are normalized to 0-1 where the highest raw ICR = 1.

    Args:
        results: List of SimulationResult from the engine.

    Returns:
        List of ModeMetrics with ICR, cost, and amplification.
    """
    if not results:
        return []

    # Find the minimum total tokens (intent-optimized baseline)
    min_tokens = min(r.total_tokens for r in results)

    # Compute raw ICR values first so we can normalize
    raw_icrs = [compute_icr(r.operations_achieved, r.total_tokens) for r in results]
    max_icr = max(raw_icrs) if raw_icrs else 1.0

    metrics = []
    for result, raw_icr in zip(results, raw_icrs):
        cost = compute_cost(result.total_input_tokens, result.total_output_tokens)
        normalized_icr = round(raw_icr / max_icr, 3) if max_icr > 0 else 0.0
        amplification = (
            round(result.total_tokens / min_tokens, 2) if min_tokens > 0 else 1.0
        )

        metrics.append(
            ModeMetrics(
                mode=result.mode,
                total_input_tokens=result.total_input_tokens,
                total_output_tokens=result.total_output_tokens,
                total_tokens=result.total_tokens,
                interaction_rounds=len(result.rounds),
                estimated_cost=cost,
                icr_score=normalized_icr,
                token_amplification=amplification,
            )
        )

    return metrics


def compute_savings(metrics: list[ModeMetrics]) -> dict:
    """Compute savings summary comparing worst to best mode.

    Returns:
        Dict with token_savings_pct, cost_savings_pct, rounds_saved, best_icr.
    """
    if not metrics:
        return {
            "token_savings_pct": 0,
            "cost_savings_pct": 0,
            "rounds_saved": 0,
            "best_icr": 0,
        }

    sorted_by_tokens = sorted(metrics, key=lambda m: m.total_tokens)
    best = sorted_by_tokens[0]
    worst = sorted_by_tokens[-1]

    token_savings = (
        (worst.total_tokens - best.total_tokens) / worst.total_tokens
    ) * 100
    cost_savings = (
        ((worst.estimated_cost - best.estimated_cost) / worst.estimated_cost) * 100
        if worst.estimated_cost > 0
        else 0
    )
    rounds_saved = worst.interaction_rounds - best.interaction_rounds
    best_icr = max(m.icr_score for m in metrics)

    return {
        "token_savings_pct": round(token_savings, 1),
        "cost_savings_pct": round(cost_savings, 1),
        "rounds_saved": rounds_saved,
        "best_icr": best_icr,
        "worst_amplification": max(m.token_amplification for m in metrics),
    }
