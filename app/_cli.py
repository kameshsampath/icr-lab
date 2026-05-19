"""CLI entry point for ICR Lab."""

import sys
from pathlib import Path

import click

# Ensure project root is importable
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@click.group(invoke_without_command=True)
@click.version_option(package_name="icr-lab")
@click.pass_context
def main(ctx):
    """ICR Lab — Intent Compression Ratio & Token Economics."""
    if ctx.invoked_subcommand is None:
        # Default: launch Streamlit app
        ctx.invoke(serve)


@main.command()
@click.argument("task")
@click.option(
    "--modes", "-m",
    multiple=True,
    help="Simulation modes to run (default: all).",
)
@click.option("--json-output", "-j", is_flag=True, help="Output results as JSON.")
def analyze(task: str, modes: tuple[str, ...], json_output: bool):
    """Run ICR analysis on a task description."""
    from examples.sample_tasks import get_operations_count
    from metrics.calculator import compute_metrics, compute_savings
    from simulations.engine import SIMULATION_MODES, run_simulation

    mode_list = list(modes) if modes else None
    operations = get_operations_count(task)
    results = run_simulation(task, operations, mode_list)
    metrics = compute_metrics(results)
    savings = compute_savings(metrics)

    if json_output:
        import json

        output = {
            "task": task,
            "operations": operations,
            "savings": savings,
            "modes": [
                {
                    "mode": m.mode,
                    "total_tokens": m.total_tokens,
                    "icr_score": m.icr_score,
                    "amplification": m.token_amplification,
                    "cost": m.estimated_cost,
                    "rounds": m.interaction_rounds,
                }
                for m in metrics
            ],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nTask: {task}")
        click.echo(f"Operations: {operations}")
        click.echo(f"\n{'Mode':<25} {'Tokens':>8} {'ICR':>6} {'Amp':>5} {'Cost':>7} {'Rounds':>6}")
        click.echo("-" * 65)
        for m in sorted(metrics, key=lambda x: x.icr_score, reverse=True):
            click.echo(
                f"{m.mode:<25} {m.total_tokens:>8,} {m.icr_score:>6.3f} "
                f"{m.token_amplification:>5.1f}x ${m.estimated_cost:>5.4f} {m.interaction_rounds:>6}"
            )
        click.echo(f"\nBest ICR: {savings['best_icr']} | "
                   f"Token savings: {savings['token_savings_pct']}% | "
                   f"Max amplification: {savings['worst_amplification']:.1f}x")


@main.command()
@click.argument("task")
@click.option("--backend", "-b", default=None, help="Backend to use (default: from config).")
def optimize(task: str, backend: str | None):
    """Optimize a verbose task into intent-compressed form."""
    from backends import get_backend

    try:
        b = get_backend(backend)
    except Exception as e:
        click.echo(f"Error loading backend: {e}", err=True)
        raise SystemExit(1)

    if not b.is_available():
        click.echo(f"Backend '{b.name}' is not available.", err=True)
        raise SystemExit(1)

    click.echo(f"Optimizing with {b.name}...")
    prompt = (
        f"Compress this task into a single intent-optimized prompt. "
        f"Preserve all operations but remove redundancy:\n\n{task}"
    )
    result = b.complete(prompt)

    click.echo(f"\nOriginal ({len(task.split())} words):")
    click.echo(f"  {task}")
    click.echo(f"\nOptimized ({len(result.text.split())} words):")
    click.echo(f"  {result.text}")
    click.echo(f"\nTokens: {result.input_tokens} in + {result.output_tokens} out = {result.total_tokens} total")


@main.command()
@click.option("--port", "-p", default=8501, help="Port for the Streamlit server.")
def serve(port: int):
    """Launch the ICR Lab Streamlit application."""
    from streamlit.web.cli import main as st_main

    app_path = str(Path(__file__).parent / "main.py")
    sys.argv = ["streamlit", "run", app_path, "--server.port", str(port)]
    st_main()
