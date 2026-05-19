"""Base protocol and types for LLM backends."""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class CompletionResult:
    """Result from an LLM completion call."""

    text: str
    input_tokens: int
    output_tokens: int
    model: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol that all LLM backends must satisfy."""

    name: str

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Send a prompt and return a completion result."""
        ...

    def is_available(self) -> bool:
        """Check if this backend is currently reachable/configured."""
        ...
