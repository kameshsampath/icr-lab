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
