"""Token counter using tiktoken BPE encoding.

Uses cl100k_base encoding (GPT-4 / GPT-4o compatible).
Tokens are counted from actual prompt text when available;
synthetic rounds fall back to the heuristic multiplier system.
"""

import tiktoken

_enc: tiktoken.Encoding | None = None


def _encoding() -> tiktoken.Encoding:
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding("cl100k_base")
    return _enc


def count_tokens(text: str) -> int:
    """Return the number of BPE tokens in text (cl100k_base encoding)."""
    return len(_encoding().encode(text))
