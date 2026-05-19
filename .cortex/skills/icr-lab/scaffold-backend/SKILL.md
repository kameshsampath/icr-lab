---
name: icr-lab/scaffold-backend
description: "Generate a new LLM backend module and register it in icr-lab.toml — supports OpenAI-compatible, SDK-based, or custom API styles. Use when: adding a new LLM provider, integrating a custom model, connecting a new API. Triggers: scaffold backend, add backend, new backend, create backend, register backend, integrate llm, add provider, new llm, connect model."
---

# Scaffold Backend

Generate a new LLM backend implementation and register it in the config.

## Workflow

1. Ask the user for:
   - Backend name (e.g., "lmstudio", "anthropic", "openai", "bedrock")
   - API style (OpenAI-compatible HTTP, SDK-based, or custom)
   - Required configuration keys
2. Generate `backends/{name}.py` implementing the `LLMBackend` protocol
3. Add `[backend.{name}]` section to `icr-lab.toml`
4. Update `backends/__init__.py` `_get_backend_class()` to include the new backend

## Example: LM Studio

When scaffolding an OpenAI-compatible HTTP backend like LM Studio, the skill generates:

**`backends/lmstudio.py`:**
```python
"""OpenAI-compatible HTTP backend (LMStudio, Ollama, vLLM, etc.)."""

import os
from urllib.request import urlopen, Request
from urllib.error import URLError
import json

from backends.base import CompletionResult, LLMBackend


class LMStudioBackend:
    """LLM backend using any OpenAI-compatible HTTP API."""

    name: str = "lmstudio"

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "local-model",
        api_key_env: str = "LLM_API_KEY",
        **kwargs,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = os.environ.get(api_key_env, "lm-studio")

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Send completion request to the OpenAI-compatible API."""
        url = f"{self.base_url}/chat/completions"
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.7),
        }).encode()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        req = Request(url, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return CompletionResult(
            text=text,
            input_tokens=usage.get("prompt_tokens", len(prompt.split()) * 4 // 3),
            output_tokens=usage.get("completion_tokens", len(text.split()) * 4 // 3),
            model=data.get("model", self.model),
        )

    def is_available(self) -> bool:
        """Check if the API endpoint is reachable."""
        try:
            req = Request(f"{self.base_url}/models", method="GET")
            with urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except (URLError, OSError):
            return False
```

**Config added to `icr-lab.toml`:**
```toml
[backend.lmstudio]
base_url = "http://localhost:1234/v1"
model = "local-model"
api_key_env = "LLM_API_KEY"
```

Use this as the pattern when scaffolding similar OpenAI-compatible backends.

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
