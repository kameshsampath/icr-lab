"""Snowflake Cortex Complete backend."""

from backends.base import CompletionResult, LLMBackend


class CortexBackend:
    """LLM backend using Snowflake Cortex Complete."""

    name: str = "cortex"

    def __init__(self, model: str = "llama3.1-8b", connection: str = "default", **kwargs):
        self.model = model
        self.connection = connection
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                from snowflake.snowpark import Session
                self._session = Session.builder.config("connection_name", self.connection).create()
            except Exception as e:
                raise ConnectionError(f"Failed to create Snowpark session: {e}") from e
        return self._session

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Call Cortex Complete via Snowpark."""
        session = self._get_session()
        from snowflake.cortex import Complete

        response = Complete(self.model, prompt, session=session)

        # Estimate tokens (Cortex doesn't always return token counts)
        input_tokens = len(prompt.split()) * 4 // 3
        output_tokens = len(response.split()) * 4 // 3

        return CompletionResult(
            text=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
        )

    def is_available(self) -> bool:
        """Check if Cortex is reachable."""
        try:
            self._get_session()
            return True
        except Exception:
            return False
