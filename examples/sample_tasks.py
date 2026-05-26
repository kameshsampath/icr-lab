"""Pre-built example tasks for ICR Lab simulations — derived from catalog.toml."""

from examples.catalog import _load, get_example

# Tasks not shown in the UI dropdown (kept in catalog for test/API use only)
_HIDDEN_TASKS: frozenset[str] = frozenset({"Build me a patient risk calculator."})

_ACTION_WORDS: frozenset[str] | None = None


def _ui_tasks() -> list[str]:
    return [t for t in _load().keys() if t not in _HIDDEN_TASKS]


def _build_action_words() -> frozenset[str]:
    """First word of every op name in catalog — auto-derived action verb set."""
    return frozenset(
        op["command"].split()[0].lower()
        for entry in _load().values()
        for op in entry.get("operations", [])
        if op.get("command")
    )


SAMPLE_TASKS = _ui_tasks()


def get_operations_count(task: str) -> int:
    """Return the number of operations for a task.

    For catalog tasks, returns the exact count from the catalog.
    For unknown tasks, estimates from word count and catalog-derived action verbs.
    """
    global _ACTION_WORDS
    e = get_example(task)
    if e:
        return len(e.get("operations", []))
    if _ACTION_WORDS is None:
        _ACTION_WORDS = _build_action_words()
    words = task.split()
    action_count = sum(1 for w in words if w.lower() in _ACTION_WORDS)
    return max(3, len(words) // 2 + action_count * 2)
