"""Snowflake Cortex Complete backend."""

import logging

from backends.base import CompletionResult, LLMBackend

logger = logging.getLogger(__name__)


class CortexBackend:
    """LLM backend using Snowflake Cortex Complete."""

    name: str = "cortex"

    def __init__(self, model: str = "claude-4-sonnet", connection: str = "default", **kwargs):
        self.model = model
        self.connection = connection
        self._session = None

    def _get_session(self):
        if self._session is None:
            try:
                from snowflake.snowpark import Session

                self._session = Session.builder.config("connection_name", self.connection).create()
            except ImportError:
                logger.error(
                    "snowflake-snowpark-python is not installed. Run: uv sync --extra cortex"
                )
                raise ConnectionError(
                    "snowflake-snowpark-python not installed. Run: uv sync --extra cortex"
                )
            except Exception as e:
                logger.error("Failed to create Snowpark session: %s", e, exc_info=True)
                raise ConnectionError(f"Failed to create Snowpark session: {e}") from e
        return self._session

    def _count_tokens(self, text: str) -> int:
        """Count tokens using Snowflake's AI_COUNT_TOKENS function."""
        session = self._get_session()
        try:
            result = session.sql(
                "SELECT AI_COUNT_TOKENS('ai_complete', ?, ?)",
                params=[self.model, text],
            ).collect()
            return result[0][0]
        except Exception as e:
            logger.debug("AI_COUNT_TOKENS failed, using estimate: %s", e)
            # Fallback: rough estimate (~1.3 tokens per word)
            return max(1, int(len(text.split()) * 1.3))

    def complete(self, prompt: str, **kwargs) -> CompletionResult:
        """Call Cortex Complete via Snowpark."""
        session = self._get_session()
        from snowflake.cortex import Complete

        try:
            response = Complete(self.model, prompt, session=session)
        except Exception as e:
            logger.error("Cortex Complete call failed (model=%s): %s", self.model, e, exc_info=True)
            raise

        input_tokens = self._count_tokens(prompt)
        output_tokens = self._count_tokens(response)

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
        except Exception as e:
            logger.warning("Cortex backend unavailable: %s", e)
            return False
