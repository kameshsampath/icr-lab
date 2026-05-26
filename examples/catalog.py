"""Catalog loader — reads examples/catalog.toml at startup and indexes by task name.

SECURITY: operation commands are display data only.
Never pass to subprocess, eval, shell, or any SQL/database execution context.
"""

import re
import tomllib
from pathlib import Path

_CATALOG: dict[str, dict] | None = None

# Matches any HTML/XML tag — stripped from command strings before storage
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _sanitize_op(op: dict) -> dict:
    """Strip null bytes, HTML tags, and cap length on op command strings at load time."""
    raw = str(op.get("command", "")).replace("\x00", "")
    clean = _HTML_TAG_RE.sub("", raw).strip()[:500]
    return {"command": clean}


_MODE_KEY_MAP = {
    "Verbose Prompting": "verbose",
    "Clarification Heavy": "clarification_heavy",
    "Context Aware": "context_aware",
    "Intent Optimized": "intent_optimized",
    "Over Compressed": "over_compressed",
    "Assumption Led": "assumption_led",
}


def _load() -> dict[str, dict]:
    global _CATALOG
    if _CATALOG is None:
        with open(Path(__file__).parent / "catalog.toml", "rb") as f:
            data = tomllib.load(f)
        _CATALOG = {
            e["task"]: {
                **e,
                "operations": [_sanitize_op(o) for o in e.get("operations", [])],
            }
            for e in data["examples"]
        }
    return _CATALOG


def get_example(task: str) -> dict | None:
    """Return the catalog entry for a task, or None. O(1) dict lookup."""
    return _load().get(task)


def get_operation_commands(task: str) -> list[str]:
    """Return list of operation command strings for a task."""
    e = get_example(task)
    if e is None:
        return []
    return [o["command"] for o in e.get("operations", [])]


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
