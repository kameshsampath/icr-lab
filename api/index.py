"""FastAPI simulation endpoint for ICR Lab.

Deterministic REST API that simulates prompting mode behaviour
so Phase A demo evidence is reproducible across runs.

SECURITY: operation names from catalog are display data only — never execute them.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so local packages are importable
# regardless of whether the file is run directly, via uvicorn, or as a
# Vercel serverless function from the api/ directory.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel, field_validator  # noqa: E402

from examples.sample_tasks import get_operations_count  # noqa: E402
from metrics.calculator import compute_metrics, compute_savings  # noqa: E402
from simulations.engine import run_simulation  # noqa: E402

app = FastAPI(title="ICR Lab Simulation API")


class SimulateRequest(BaseModel):
    task: str
    operations: int | None = None  # auto-derived from catalog when omitted
    requirements: list[str] = []
    modes: list[str] | None = None
    mode_operations_achieved: dict[str, int] = {}
    assumption_accuracy: float = 1.0  # 0.0 = all wrong, 1.0 = all correct

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        v = v.replace("\x00", "").strip()
        if not v:
            raise ValueError("task must not be empty")
        if len(v) > 2000:
            raise ValueError("task must be ≤ 2000 characters")
        return v

    @field_validator("requirements", mode="before")
    @classmethod
    def sanitize_requirements(cls, v: list) -> list:
        return [str(r).replace("\x00", "").strip()[:500] for r in v]

    @field_validator("assumption_accuracy")
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("assumption_accuracy must be between 0.0 and 1.0")
        return round(v, 4)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simulate")
def simulate(req: SimulateRequest):
    # Resolve operations: use explicit value or derive from catalog/heuristic
    operations = (
        req.operations if req.operations is not None else get_operations_count(req.task)
    )

    # Run simulation for the requested modes
    results = run_simulation(
        req.task, operations, req.modes, assumption_accuracy=req.assumption_accuracy
    )

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
        result_for_mode = next((r for r in results if r.mode == m.mode), None)
        token_metrics[m.mode] = {
            "input_tokens": m.total_input_tokens,
            "output_tokens": m.total_output_tokens,
            "total_tokens": m.total_tokens,
            "interaction_rounds": m.interaction_rounds,
            "icr": m.icr_score,
            "raw_icr": m.raw_icr_score,
            "token_amplification": m.token_amplification,
            "estimated_cost": m.estimated_cost,
            "total_assumptions": result_for_mode.total_assumptions
            if result_for_mode
            else 0,
            "wrong_assumptions": result_for_mode.wrong_assumptions
            if result_for_mode
            else 0,
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
                "token_source": rnd.token_source,
                "assumptions": rnd.assumptions,
            }
            for rnd in r.rounds
        ]

    # Build requirements_coverage: first ops_achieved reqs are True, rest False
    requirements_coverage: dict[str, dict] = {}
    for r in results:
        ops_achieved = r.operations_achieved
        coverage = {
            req_name: (i < ops_achieved) for i, req_name in enumerate(req.requirements)
        }
        requirements_coverage[r.mode] = coverage

    return {
        "task": req.task,
        "operations": operations,
        "token_metrics": token_metrics,
        "trace": trace,
        "requirements_coverage": requirements_coverage,
        "savings_hypothesis": savings,
    }
