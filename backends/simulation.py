"""Simulation backend — wraps the existing deterministic engine."""

from backends.base import CompletionResult, LLMBackend


class SimulationBackend:
    """Backend that uses the deterministic simulation engine.

    This is always available and requires no external dependencies.
    It doesn't call any LLM — instead it generates synthetic token
    traces using the simulation engine.
    """

    name: str = "simulation"

    def __init__(self, **kwargs):
        pass

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Simulate a completion using deterministic token estimation."""
        # Approximate token counts based on prompt characteristics
        input_tokens = len(prompt.split()) * 4 // 3
        output_tokens = input_tokens * 2  # Simulated response is ~2x input

        return CompletionResult(
            text=f"[simulation] Processed: {prompt[:80]}...",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="deterministic-v1",
        )

    def is_available(self) -> bool:
        """Simulation is always available."""
        return True
