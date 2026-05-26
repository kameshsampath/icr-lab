"""Catalog loader — reads examples/catalog.toml at startup and indexes by task name."""

import tomllib
from pathlib import Path

_CATALOG: dict[str, dict] | None = None

_MODE_KEY_MAP = {
    "Verbose Prompting": "verbose",
    "Clarification Heavy": "clarification_heavy",
    "Context-Aware": "context_aware",
    "Intent-Optimized": "intent_optimized",
    "Over-Compressed": "over_compressed",
    "Assumption-Led": "assumption_led",
}


def _load() -> dict[str, dict]:
    global _CATALOG
    if _CATALOG is None:
        with open(Path(__file__).parent / "catalog.toml", "rb") as f:
            _CATALOG = {e["task"]: e for e in tomllib.load(f)["examples"]}
    return _CATALOG


def get_example(task: str) -> dict | None:
    """Return the catalog entry for a task, or None. O(1) dict lookup."""
    return _load().get(task)


def get_operation_names(task: str) -> list[str]:
    """Return list of operation name strings for a task."""
    e = get_example(task)
    if e is None:
        return []
    return [o["name"] for o in e.get("operations", [])]


def get_operation_types(task: str) -> list[str]:
    """Return list of operation type strings for a task."""
    e = get_example(task)
    if e is None:
        return []
    return [o["type"] for o in e.get("operations", [])]


def get_optimized_prompt(task: str) -> str:
    """Return the intent-optimized prompt for a task."""
    e = get_example(task)
    if e:
        val = e.get("prompts", {}).get("intent_optimized", "")
        return val.strip() if val else task
    return task


def get_verbose_prompt(task: str) -> str:
    """Return the verbose prompt for a task."""
    e = get_example(task)
    if e:
        val = e.get("prompts", {}).get("verbose", "")
        return val.strip() if val else task
    return task


def get_prompt_for_mode(task: str, mode: str) -> str | list[str]:
    """Return the prompt(s) for a task and mode.

    Returns list[str] for multi-round modes (Clarification Heavy, Assumption-Led),
    str for single-prompt modes.
    """
    e = get_example(task)
    key = _MODE_KEY_MAP.get(mode)
    if e and key:
        val = e.get("prompts", {}).get(key)
        if val is not None:
            if isinstance(val, list):
                return [v.strip() if isinstance(v, str) else v for v in val]
            return val.strip() if isinstance(val, str) else val

    # Synthetic fallbacks for unknown tasks
    if mode == "Verbose Prompting":
        return get_verbose_prompt(task)
    if mode == "Clarification Heavy":
        return [
            f"Can you help with: {task}?",
            "What specifically do you need?",
            f"I need {task.lower()}.",
            "Any particular constraints?",
            "Just make sure it works correctly.",
            "OK, proceeding with the standard approach.",
        ]
    if mode == "Context-Aware":
        return f"{task}. Handle dependencies automatically, validate on completion."
    if mode == "Assumption-Led":
        return [
            f"Assuming standard defaults. Proceeding with: {task}.",
            "Correction: please adjust based on actual environment.",
            "Re-executing with corrections applied.",
        ]
    return get_optimized_prompt(task)
