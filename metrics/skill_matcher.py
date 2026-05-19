"""Skill discovery and matching for ICR Lab.

Discovers installed skills via `cortex skill list` (live), falls back to
static pattern matching when CLI is unavailable (e.g., deployed on Streamlit Cloud).
"""

import logging
import re
import subprocess
from pathlib import Path

from metrics.ops_patterns import count_ops_in_text

logger = logging.getLogger(__name__)

# Which platforms support reusable skills
PLATFORM_SKILL_SUPPORT = {
    "cortex": True,
    "claude": True,
    "codex": True,
    "gemini": True,
    "lmstudio": False,
    "simulation": False,
}

# Static trigger patterns — match task text to potential skill domains
SKILL_TRIGGER_PATTERNS = {
    "programmatic-access-token": [
        r"service.user",
        r"network.rule",
        r"auth.policy",
        r"PAT\b",
        r"token",
        r"CREATE USER",
        r"CREATE ROLE",
        r"GRANT ROLE",
    ],
    "external-volume": [
        r"external.volume",
        r"IAM",
        r"trust.policy",
        r"S3\b",
        r"STORAGE_BASE_URL",
        r"azure://",
        r"gs://",
        r"s3://",
    ],
    "network-rule": [
        r"network.rule",
        r"EGRESS",
        r"HOST_PORT",
        r"external.access.integration",
        r"EAI\b",
        r"INGRESS",
        r"PrivateLink",
    ],
    "iceberg": [
        r"iceberg",
        r"ICEBERG_TABLE",
        r"catalog.integration",
        r"external.volume",
        r"parquet",
        r"BASE_LOCATION",
    ],
    "governance-setup": [
        r"SYSTEM\$CLASSIFY",
        r"masking.policy",
        r"row.access",
        r"object.tag",
        r"PII",
        r"SENSITIVE",
        r"RBAC",
    ],
    "spcs-deploy": [
        r"compute.pool",
        r"CREATE SERVICE",
        r"image.repository",
        r"SPCS",
        r"container",
        r"endpoint",
        r"Snowpark Container",
    ],
    "cortex-agent": [
        r"cortex.agent",
        r"Cortex Complete",
        r"Cortex Search",
        r"handler",
        r"agent",
        r"CREATE CORTEX",
        r"SEARCH SERVICE",
        r"RAG",
    ],
    "data-pipeline": [
        r"dynamic.table",
        r"CDC",
        r"change data capture",
        r"incremental.refresh",
        r"streaming",
        r"Kafka",
        r"Debezium",
    ],
}


def discover_skills_live() -> list[dict]:
    """Run `cortex skill list` and parse installed skills.

    Returns list of {"name": ..., "path": ..., "type": ...} or empty list if unavailable.
    """
    try:
        result = subprocess.run(
            ["cortex", "skill", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            return []
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    skills = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("─") or line.startswith("="):
            continue

        parts = re.split(r"\s{2,}|\t", line)
        if len(parts) >= 2:
            name = parts[0].strip()
            path = parts[1].strip()
            skill_type = parts[2].strip() if len(parts) >= 3 else "unknown"
            if name and path and not name.startswith("#"):
                skills.append({"name": name, "path": path, "type": skill_type})
        elif ":" in line:
            name, _, path = line.partition(":")
            name = name.strip()
            path = path.strip()
            if name and path:
                skills.append({"name": name, "path": path, "type": "unknown"})

    return skills


def match_skills_static(text: str) -> list[dict]:
    """Match text against static skill trigger patterns.

    Returns skills where 2+ patterns match, sorted by match strength.
    """
    suggestions = []

    for skill_key, patterns in SKILL_TRIGGER_PATTERNS.items():
        match_count = 0
        matched_patterns = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match_count += 1
                matched_patterns.append(pattern)

        if match_count >= 2:
            # Estimate ICR: count domain-specific operations
            domain_ops = 0
            for pattern in patterns:
                domain_ops += len(re.findall(pattern, text, re.IGNORECASE))

            icr_estimate = f"~1:{domain_ops}" if domain_ops > 0 else "N/A"

            suggestions.append({
                "skill": f"${skill_key}",
                "match_count": match_count,
                "total_patterns": len(patterns),
                "matched_patterns": matched_patterns[:3],
                "icr_estimate": icr_estimate,
                "domain_ops": domain_ops,
            })

    suggestions.sort(key=lambda s: s["match_count"], reverse=True)
    return suggestions


def match_skills(text: str) -> list[dict]:
    """Match task text to skills using live discovery + static fallback.

    Tries `cortex skill list` first for availability info, then uses
    static pattern matching for the actual recommendations.
    """
    # Always do static matching (works everywhere)
    suggestions = match_skills_static(text)

    # Try live discovery to check which suggested skills are actually installed
    live_skills = discover_skills_live()
    if live_skills:
        installed_names = {s["name"] for s in live_skills}
        for suggestion in suggestions:
            skill_name = suggestion["skill"].lstrip("$")
            suggestion["available"] = any(
                skill_name in name for name in installed_names
            )
    else:
        for suggestion in suggestions:
            suggestion["available"] = None  # Unknown

    return suggestions


def platform_supports_skills(backend_name: str) -> bool:
    """Check if a backend platform supports reusable skills."""
    return PLATFORM_SKILL_SUPPORT.get(backend_name.lower(), False)
