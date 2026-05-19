"""LLM Backend registry for ICR Lab.

Reads available backends from icr-lab.toml [icr-lab.backend.*] sections.
"""

import logging

from backends.base import CompletionResult, LLMBackend
from backends.config import load_config

logger = logging.getLogger(__name__)

__all__ = ["CompletionResult", "LLMBackend", "get_backend", "list_backends"]


def list_backends() -> list[tuple[str, bool, str]]:
    """List all registered backends with availability status.

    Returns:
        List of (name, usable, reason) tuples.
        usable=True means the backend can be instantiated.
    """
    config = load_config()
    backend_sections = {
        k.removeprefix("backend."): v
        for k, v in config.items()
        if k.startswith("backend.") and isinstance(v, dict)
    }

    results = []
    for name, settings in backend_sections.items():
        try:
            _get_backend_class(name)
            results.append((name, True, "available"))
        except ImportError as e:
            logger.warning("Backend '%s' unavailable (import error): %s", name, e)
            results.append((name, False, str(e)))
        except Exception as e:
            logger.error("Backend '%s' failed to load: %s", name, e, exc_info=True)
            results.append((name, False, f"error: {e}"))
    return results


def _get_backend_class(name: str):
    """Import and return the backend class for a given name."""
    if name == "simulation":
        from backends.simulation import SimulationBackend
        return SimulationBackend
    elif name == "cortex":
        from backends.cortex import CortexBackend
        return CortexBackend
    else:
        raise ImportError(f"Unknown backend: {name}. Use `$icr-lab scaffold-backend` to add it.")


def get_backend(name: str | None = None) -> "LLMBackend":
    """Instantiate and return a backend by name.

    Args:
        name: Backend name from icr-lab.toml. If None, uses [backend].default.

    Returns:
        An initialized LLMBackend instance.
    """
    config = load_config()
    if name is None:
        name = config.get("backend", {}).get("default", "simulation")

    cls = _get_backend_class(name)
    settings = config.get(f"backend.{name}", {})
    return cls(**settings)
