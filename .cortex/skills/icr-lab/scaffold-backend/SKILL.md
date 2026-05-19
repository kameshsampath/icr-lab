---
name: icr-lab/scaffold-backend
description: Generate a new LLM backend module and register it in icr-lab.toml
triggers:
  - scaffold backend
  - add backend
  - new backend
  - create backend
---

# Scaffold Backend

Generate a new LLM backend implementation and register it in the config.

## Workflow

1. Ask the user for:
   - Backend name (e.g., "anthropic", "openai", "bedrock")
   - API style (OpenAI-compatible HTTP, SDK-based, or custom)
   - Required configuration keys
2. Generate `backends/{name}.py` implementing the `LLMBackend` protocol
3. Add `[backend.{name}]` section to `icr-lab.toml`
4. Update `backends/__init__.py` `_get_backend_class()` to include the new backend

## Template

```python
"""{{name}} backend for ICR Lab."""

import os
from backends.base import CompletionResult, LLMBackend


class {{ClassName}}Backend:
    """LLM backend using {{name}}."""

    name: str = "{{name}}"

    def __init__(self, {{config_params}}, **kwargs):
        # Initialize from config
        ...

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Send prompt to {{name}} and return completion."""
        ...

    def is_available(self) -> bool:
        """Check if {{name}} is reachable."""
        ...
```

## Registration

After generating the .py file:

1. Add to `backends/__init__.py`:
```python
elif name == "{{name}}":
    from backends.{{name}} import {{ClassName}}Backend
    return {{ClassName}}Backend
```

2. Add to `icr-lab.toml`:
```toml
[backend.{{name}}]
# Configuration keys here
```

## Validation

After scaffolding, verify:
```bash
cd /Users/ksampath/mylabs/worktrees/icr-lab-feature-coco
python -c "from backends import list_backends; print(list_backends())"
```
