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
4. **Optional: Scaffold** — If user wants a non-bundled backend, route to `$icr-lab scaffold-backend`
5. **Optional: Test Connection** — If user picks `cortex`, run `snow connection test`

## Implementation

```python
import sys
sys.path.insert(0, "<project_root>")

from backends.config import validate_config, ensure_config, load_config, save_backend_section
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

### 4. Cortex Connection Test

If user selects `cortex` as default:
```bash
snow connection test
```

If it fails, suggest:
- Check `~/.snowflake/connections.toml`
- Or use `snow connection add` to configure
- Or switch default to `simulation`

### 5. Summary

Print final config state:
- Config path
- Default backend
- Available backends with status
- Any warnings

## When to Use This Skill

- First time running ICR Lab
- After cloning the repo (icr-lab.toml is gitignored)
- Config file got corrupted or accidentally deleted
- Want to switch default backend
- Troubleshooting "backend unavailable" errors
