"""FastAPI simulation endpoint for ICR Lab.

Deterministic REST API that simulates prompting mode behaviour
so Phase A demo evidence is reproducible across runs.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from metrics.calculator import compute_metrics, compute_savings
from simulations.engine import run_simulation

app = FastAPI(title="ICR Lab Simulation API")


class SimulateRequest(BaseModel):
    task: str
    operations: int
    requirements: list[str] = []
    modes: list[str] | None = None
    mode_operations_achieved: dict[str, int] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simulate")
def simulate(req: SimulateRequest):
    # Run simulation for the requested modes
    results = run_simulation(req.task, req.operations, req.modes)

    # Override per-mode operations_achieved BEFORE compute_metrics
    if req.mode_operations_achieved:
        for r in results:
            if r.mode in req.mode_operations_achieved:
                r.operations_achieved = req.mode_operations_achieved[r.mode]

    metrics = compute_metrics(results)
    savings = compute_savings(metrics)

    # Add monthly projection (worst - best cost) × 1 000 runs
    if metrics:
        sorted_by_tokens = sorted(metrics, key=lambda m: m.total_tokens)
        best_cost = sorted_by_tokens[0].estimated_cost
        worst_cost = sorted_by_tokens[-1].estimated_cost
        monthly_savings = max(0.0, worst_cost - best_cost) * 1000
    else:
        monthly_savings = 0.0
    savings["monthly_projection_1k_runs"] = round(monthly_savings, 2)

    # Build token_metrics dict (field names match test assertions)
    token_metrics: dict[str, dict] = {}
    for m in metrics:
        token_metrics[m.mode] = {
            "input_tokens": m.total_input_tokens,
            "output_tokens": m.total_output_tokens,
            "total_tokens": m.total_tokens,
            "interaction_rounds": m.interaction_rounds,
            "icr": m.icr_score,
            "raw_icr": m.raw_icr_score,
            "token_amplification": m.token_amplification,
            "estimated_cost": m.estimated_cost,
        }

    # Build trace dict (round field names match test assertions)
    trace: dict[str, list] = {}
    for r in results:
        trace[r.mode] = [
            {
                "round": rnd.round_number,
                "input_tokens": rnd.input_tokens,
                "output_tokens": rnd.output_tokens,
                "cumulative_tokens": rnd.cumulative_tokens,
                "description": rnd.description,
                "prompt_text": rnd.prompt_text,
            }
            for rnd in r.rounds
        ]

    # Build requirements_coverage: first ops_achieved reqs are True, rest False
    requirements_coverage: dict[str, dict] = {}
    for r in results:
        ops_achieved = r.operations_achieved
        coverage = {
            req_name: (i < ops_achieved)
            for i, req_name in enumerate(req.requirements)
        }
        requirements_coverage[r.mode] = coverage

    return {
        "task": req.task,
        "operations": req.operations,
        "token_metrics": token_metrics,
        "trace": trace,
        "requirements_coverage": requirements_coverage,
        "savings_hypothesis": savings,
    }
