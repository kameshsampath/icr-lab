---
name: icr-lab/setup
description: "Initialize or repair ICR Lab configuration. Use when: first run, config missing, config corrupted, want to choose default backend, reset icr-lab.toml, configure ICR Lab. Triggers: icr-lab setup, icr-lab configure, icr-lab init, reset icr config, fix icr config, configure icr, setup icr, initialize icr lab."
---

# ICR Lab Setup

Initialize, validate, or repair the ICR Lab configuration.

## Workflow

1. **Validate** — Run `validate_config()` to check current state
2. **Repair/Create** — If invalid or missing, call `ensure_config()` (backs up corrupted files as `.bak`)
3. **Select Default Backend** — Show `list_backends()` and let user pick
4. **Select Model** — If `cortex` chosen, let user pick from available models
5. **Optional: Test Connection** — If user picks `cortex`, run `snow connection test`
6. **Install Dependencies** — If `cortex` chosen, ensure `snowflake-snowpark-python` is installed
7. **Optional: Create Database** — Offer to create `{PREFIX}_ICR_LAB` in Snowflake
8. **Configure Deploy** — Auto-fill from connection info, ask user for missing fields (warehouse, compute_pool)
9. **Optional: Scaffold** — If user wants a non-bundled backend, route to `$icr-lab scaffold-backend`

## Implementation

```python
import sys
sys.path.insert(0, "<project_root>")

from backends.config import (
    validate_config, ensure_config, load_config,
    save_backend_section, _get_snowflake_connection_info,
)
from backends import list_backends
```

## Steps

### 1. Check Config Status

```python
valid, issues = validate_config()
```

Report to user:
- If valid: "Config OK — icr-lab.toml is valid."
- If issues: List them and ask: "Overwrite with fresh defaults? (old saved as .bak)"

### 2. Ensure Config Exists

If user confirms repair or config is missing:
```python
path = ensure_config(force=user_wants_clean_reset)
```

### 3. Choose Default Backend

Show available backends:
```python
backends = list_backends()
# Present as options: simulation (always), cortex (if Snowflake configured), lmstudio (if local server)
```

Ask: "Which backend should be the default?"

Update the default in config if changed.

### 4. Model Selection (Cortex only)

If user selects `cortex` as default backend, ask which model to use:

Present these options grouped by size:
- **Large:** `llama3.1-70b`, `mistral-large2`
- **Medium:** `llama3.1-8b`, `mistral-7b`
- **Small:** `llama3.2-1b`

Default suggestion: `llama3.1-8b` (good balance of quality and speed).

After selection, update the config:
```python
save_backend_section("cortex", {"model": chosen_model, "connection": "default", "database": f"{prefix}_ICR_LAB", "schema": "PUBLIC"})
```

### 5. Cortex Connection Test

If user selects `cortex` as default:
```bash
snow connection test
```

If it fails, suggest:
- Check `~/.snowflake/connections.toml`
- Or use `snow connection add` to configure
- Or switch default to `simulation`

### 6. Install Dependencies (Cortex only)

If user selected `cortex`, check whether `snowflake-snowpark-python` is importable:

```python
try:
    import snowflake.snowpark
    # Already installed
except ImportError:
    # Not installed — need to install cortex extra
    pass
```

If not installed, inform the user and run:
```bash
uv sync --extra cortex
```

If not using `uv`, fall back to:
```bash
pip install "icr-lab[cortex]"
```

After install, verify the import succeeds. If it still fails, report the error and suggest troubleshooting.

### 7. Database Setup (Cortex only)

If `cortex` is one of the available backends, ask:

> "Would you like to create the database `{PREFIX}_ICR_LAB` in Snowflake now?"

- If **yes**: Execute via Snowflake SQL:
  ```sql
  CREATE DATABASE IF NOT EXISTS {prefix}_ICR_LAB;
  CREATE SCHEMA IF NOT EXISTS {prefix}_ICR_LAB.PUBLIC;
  ```
- If **no**: Skip — user will create it later or it already exists.

### 8. Deploy Configuration

Auto-fill `[icr-lab.deploy]` fields from `snow connection test` output where available.
Ask user for anything still empty.

```python
info = _get_snowflake_connection_info()
# info = {"user": "KAMESHS", "connection": "devrel-ent", "warehouse": "", ...}
```

Fields to configure:
- **database**: Default `{PREFIX}_ICR_LAB` (already set from step 6)
- **schema**: Default `PUBLIC`
- **warehouse**: Use value from `info["warehouse"]` if available. If empty, ask:
  > "Which warehouse should be used for deployments?"
- **compute_pool**: Always ask (not available from connection test):
  > "Which compute pool for container services? (leave blank to skip)"
- **connection**: Use `info["connection"]` (the active Snowflake CLI connection name)

Update the config file with the collected values.

### 9. Summary & Getting Started

Print final config state:
- Config path
- Default backend
- Available backends with status
- Any warnings

Then display a "Getting Started" block (markdown):

```markdown
## ✅ Setup Complete!

**Config:** `./icr-lab.toml`
**Default backend:** {default_backend}
**Connection:** {connection_name}

### Start the app

    task serve        # or: uv run icr-lab serve

Opens at http://localhost:8501

### Other commands

    uv run icr-lab analyze "Deploy payment service with autoscaling"
    uv run icr-lab optimize "Your verbose prompt here..."

### Need help?

    $icr-lab              # show all ICR Lab skills
    $icr-lab scaffold-backend   # add a custom backend
```

## When to Use This Skill

- First time running ICR Lab
- After cloning the repo (icr-lab.toml is gitignored)
- Config file got corrupted or accidentally deleted
- Want to switch default backend
- Troubleshooting "backend unavailable" errors
