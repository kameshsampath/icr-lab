# AGENTS.md

## Purpose

This repository is the ICR Lab — an interactive simulator for Intent Compression Ratio (ICR)
and token economics in AI systems.

It is a live demo at https://icr-lab.streamlit.app/ and is deployed automatically on each push to `main`.

## Project Structure

- `app/` — Streamlit application (pages, CLI entry points, FastAPI endpoint)
- `simulations/` — Simulation engine and interaction modes
- `metrics/` — ICR calculator, token counter, cost estimation
- `examples/` — Catalog of example tasks and prompt templates (TOML + loader)
- `visuals/` — Plotly chart builders
- `tests/` — Test suite (pytest + httpx TestClient)

## Development

Always use `uv` as the Python package manager:
- `uv add <pkg>` — add a runtime dependency
- `uv add <pkg> --dev` — add a dev dependency
- `uv run <cmd>` — run a command in the project environment

Test locally before pushing:
```
uv run streamlit run app/main.py
```

Run the simulation API:
```
task api
```

Run tests:
```
task test
```

## GitHub

- All GitHub operations must use the `kameshsampath` account.
- Always verify `gh auth status` shows `kameshsampath` as the active account before any GitHub operations.
- If the active account is not `kameshsampath`, switch with: `gh auth switch --user kameshsampath`

## Commits

- Always use [Conventional Commits](https://www.conventionalcommits.org/) style.
- Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `build`, `ci`, `perf`, `style`, `revert`
- Always add the trailer: `Made with Cortex Code`
- Example:
  ```
  feat: add assumption-led simulation mode

  Made with Cortex Code
  ```

## Pre-commit

- All commits and code changes **must pass pre-commit hooks** before being committed.
- Install hooks: `pre-commit install && pre-commit install --hook-type commit-msg`
- Verify before committing: `pre-commit run --all-files`
- Task completion requires all pre-commit hooks to pass — do not mark a task done if hooks are failing.

## Deployment

The app is deployed to Streamlit Cloud automatically on each push to `main`.
Always test locally with `uv run streamlit run app/main.py` before pushing.
