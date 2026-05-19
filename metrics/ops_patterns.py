"""Operation patterns for ICR calculation.

Adapted from workflow-skill-evaluator (Snowflake-Labs).
Counts discrete operations in text to estimate intent density.
"""

import re

# Canonical set of operation patterns used for ICR estimation.
OPS_PATTERNS = {
    "SQL DDL/DML": re.compile(
        r"\b(CREATE|ALTER|DROP|GRANT|REVOKE|INSERT|MERGE|UPDATE|DELETE|TRUNCATE|COPY INTO)\b",
        re.IGNORECASE,
    ),
    "Snowflake CLI": re.compile(
        r"\b(snow\s+\w+|sfutils-\w+|snowsql)\b",
        re.IGNORECASE,
    ),
    "Cloud CLIs": re.compile(
        r"\b(aws\s+\w+|az\s+\w+|gcloud\s+\w+)\b",
        re.IGNORECASE,
    ),
    "HTTP/API": re.compile(
        r"\b(curl|wget|https?://|fetch|requests\.)\b",
        re.IGNORECASE,
    ),
    "Container ops": re.compile(
        r"\b(docker\s+\w+|podman\s+\w+|kubectl\s+\w+)\b",
        re.IGNORECASE,
    ),
    "Shell ops": re.compile(
        r"\b(mkdir|chmod|cp|rm|mv|tar|zip)\b",
        re.IGNORECASE,
    ),
    "Dev tools": re.compile(
        r"\b(uv\s+run|pip\s+install|npm\s+\w+|make\s+\w+)\b",
        re.IGNORECASE,
    ),
}


def count_ops_in_text(text: str) -> int:
    """Count total operations across all pattern categories."""
    total = 0
    for pat in OPS_PATTERNS.values():
        total += len(pat.findall(text))
    return total


def count_ops_by_type(text: str) -> dict[str, int]:
    """Count operations grouped by category.

    Returns dict like {"SQL DDL/DML": 3, "Container ops": 2}.
    Only includes categories with > 0 matches.
    """
    result = {}
    for category, pat in OPS_PATTERNS.items():
        count = len(pat.findall(text))
        if count > 0:
            result[category] = count
    return result
