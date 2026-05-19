"""Skill discovery and matching for ICR Lab.

Discovers installed skills via `cortex skill list` (live), falls back to
static pattern matching when CLI is unavailable (e.g., deployed on Streamlit Cloud).

When an LLM backend is active (not simulation), uses the backend to semantically
match task text against discovered skill frontmatter for more accurate results.
"""

import json
import logging
import re
import subprocess
from pathlib import Path

import streamlit as st

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
    current_section = "unknown"

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("─") or line.startswith("="):
            continue

        # Detect section headers like [BUNDLED], [PROJECT], [EXTERNAL]
        if line.startswith("[") and line.endswith("]"):
            current_section = line.strip("[]").lower()
            continue

        # Parse "- name: /path" lines
        if line.startswith("- ") and ":" in line:
            rest = line[2:]  # strip "- "
            name, _, path = rest.partition(":")
            name = name.strip()
            path = path.strip()
            if name and path:
                skills.append({"name": name, "path": path, "type": current_section})

    return skills


def parse_skill_frontmatter(path: str | Path) -> dict | None:
    """Read a SKILL.md file and extract YAML frontmatter fields.

    Returns {"name": ..., "description": ..., "triggers": [...]} or None.
    """
    path = Path(path)
    if not path.exists():
        return None

    try:
        content = path.read_text()
    except OSError:
        return None

    # Extract YAML frontmatter between --- markers
    match = re.match(r"^---\s*\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter = match.group(1)
    info: dict = {"name": "", "description": "", "triggers": []}

    for line in frontmatter.splitlines():
        if line.startswith("name:"):
            info["name"] = line.split(":", 1)[1].strip().strip("\"'")
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip("\"'")
            info["description"] = desc
            # Extract triggers from description if present
            trigger_match = re.search(r"Triggers?:\s*(.+?)\.?\s*$", desc, re.IGNORECASE)
            if trigger_match:
                triggers = [t.strip() for t in trigger_match.group(1).split(",")]
                info["triggers"] = triggers

    return info if info["name"] else None


@st.cache_data(ttl=3600, show_spinner="Discovering installed skills...")
def _discover_skill_frontmatter() -> list[dict]:
    """Find all SKILL.md files and parse their frontmatter.

    Prefers live-discovered paths from `cortex skill list` for accurate results.
    Falls back to local filesystem scan when CLI is unavailable.
    Cached for 1 hour to avoid re-scanning on every call.
    """
    skills_info = []
    seen_names: set[str] = set()

    # Prefer live discovery — gives us accurate paths including bundled skills
    live_skills = discover_skills_live()
    if live_skills:
        for skill in live_skills:
            skill_path = Path(skill["path"])
            # Check for SKILL.md in the skill directory and subdirectories
            for skill_md in [skill_path / "SKILL.md", *skill_path.glob("*/SKILL.md")]:
                info = parse_skill_frontmatter(skill_md)
                if info and info["name"] not in seen_names:
                    info["type"] = skill["type"]
                    seen_names.add(info["name"])
                    skills_info.append(info)
        if skills_info:
            return skills_info

    # Fallback: local filesystem scan
    search_roots = [
        Path.cwd() / ".cortex" / "skills",
        Path.home() / ".cortex" / "skills",
    ]

    for root in search_roots:
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            info = parse_skill_frontmatter(skill_md)
            if info and info["name"] not in seen_names:
                seen_names.add(info["name"])
                skills_info.append(info)

    return skills_info


def match_skills_with_llm(text: str, skills_info: list[dict], backend) -> list[dict]:
    """Use an LLM backend to semantically match task text to skills.

    Args:
        text: The task description text.
        skills_info: List of skill info dicts with name/description/triggers.
        backend: An LLM backend instance (must have .complete() method).

    Returns:
        List of matched skill dicts compatible with match_skills_static output.
    """
    if not skills_info:
        return []

    # Build skill catalog for the prompt
    catalog_lines = []
    for s in skills_info:
        triggers_str = ", ".join(s["triggers"][:5]) if s["triggers"] else "none listed"
        catalog_lines.append(
            f"- {s['name']}: {s['description'][:120]}... [triggers: {triggers_str}]"
        )

    catalog = "\n".join(catalog_lines)

    # Build allowlist of valid skill names from catalog
    valid_skill_names = {s["name"] for s in skills_info}

    prompt = (
        "You are a deterministic skill matching engine for "
        "implementation planning.\n"
        "Given an optimized task intent and a catalog of available skills, "
        "select only the skills needed to implement the task.\n\n"
        "Matching rules:\n"
        "- Match skills based on explicit task operations, services, APIs, "
        "objects, models, constraints, deployment targets, auth, memory, "
        "and guardrails\n"
        "- Prefer exact domain/tool matches over generic semantic similarity\n"
        "- Do NOT select a skill unless the task contains clear evidence for it\n"
        "- Do NOT infer missing requirements\n"
        "- Do NOT select broad/generic skills when a more specific catalog skill matches\n"
        "- Include prerequisite/supporting skills only when directly required by the task flow\n"
        "- Preserve task order by assigning lower order values to earlier implementation steps\n"
        "- Return [] if no catalog skills are clearly relevant\n\n"
        "Confidence guidance:\n"
        "- 0.90-1.00: explicit exact match to operation/service/API/object/model\n"
        "- 0.75-0.89: strong semantic match with clear implementation relevance\n"
        "- 0.50-0.74: partial match or supporting prerequisite directly implied by task\n"
        "- <0.50: omit\n\n"
        "Output rules:\n"
        "- Output ONLY valid JSON, no markdown, no prose\n"
        "- Return a JSON array sorted by implementation order, then confidence descending\n"
        "- Only include skills with confidence >= 0.5\n"
        "- Each object must have exactly these fields: "
        '"skill", "confidence", "reason", "evidence", "order"\n'
        "- skill: exact skill name from catalog\n"
        "- confidence: number from 0.0 to 1.0\n"
        "- reason: brief reason for why the skill is needed\n"
        "- evidence: exact task phrase or term that triggered the match\n"
        "- order: integer starting at 1\n\n"
        f"SKILL CATALOG:\n{catalog}\n\n"
        f"OPTIMIZED TASK INTENT:\n{text[:2000]}\n\n"
        "Return JSON now."
    )

    try:
        result = backend.complete(prompt)
        response_text = result.text.strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```\w*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        matches = json.loads(response_text)
        if not isinstance(matches, list):
            return []

        # Convert to standard format
        suggestions = []
        for m in matches:
            if not isinstance(m, dict) or "skill" not in m:
                continue
            confidence = float(m.get("confidence", 0.5))
            if confidence < 0.5:
                continue
            skill_name = m["skill"].lstrip("$")
            # Reject hallucinated skills not in the catalog
            if skill_name not in valid_skill_names:
                continue
            suggestions.append(
                {
                    "skill": f"${skill_name}",
                    "match_count": int(confidence * 10),
                    "total_patterns": 10,
                    "matched_patterns": [m.get("reason", "LLM match")],
                    "icr_estimate": "LLM",
                    "domain_ops": 0,
                    "confidence": confidence,
                    "source": "llm",
                }
            )

        suggestions.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        return suggestions

    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        logger.warning("LLM skill matching failed to parse response: %s", e)
        return []
    except Exception as e:
        logger.warning("LLM skill matching error: %s", e)
        return []


@st.cache_data(show_spinner=False)
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

            suggestions.append(
                {
                    "skill": f"${skill_key}",
                    "match_count": match_count,
                    "total_patterns": len(patterns),
                    "matched_patterns": matched_patterns[:3],
                    "icr_estimate": icr_estimate,
                    "domain_ops": domain_ops,
                    "source": "static",
                }
            )

    suggestions.sort(key=lambda s: s["match_count"], reverse=True)
    return suggestions


def match_skills(text: str, backend_name: str | None = None) -> list[dict]:  # noqa: PLR0912
    """Match task text to skills using LLM (when available) + static fallback.

    Args:
        text: The task description text to match.
        backend_name: Name of the active backend. If set and not "simulation",
            attempts LLM-assisted matching first, merging with static results.

    Returns:
        List of skill match dicts sorted by relevance.
    """
    # Always do static matching (works everywhere)
    static_suggestions = match_skills_static(text)

    # Try LLM-assisted matching when a real backend is active
    llm_suggestions: list[dict] = []
    if backend_name and backend_name.lower() != "simulation":
        try:
            from backends import get_backend  # noqa: PLC0415

            backend = get_backend(backend_name)
            if backend.is_available():
                skills_info = _discover_skill_frontmatter()
                if skills_info:
                    llm_suggestions = match_skills_with_llm(text, skills_info, backend)
        except Exception as e:
            logger.warning("LLM skill matching unavailable, using static: %s", e)

    # Merge: LLM results take priority, add static results not already covered
    if llm_suggestions:
        llm_skill_names = {s["skill"] for s in llm_suggestions}
        # Build token set from LLM skill names for fuzzy dedup
        # e.g. "$deploy-to-spcs" -> {"deploy", "to", "spcs"}
        llm_name_tokens = set()
        for name in llm_skill_names:
            llm_name_tokens.update(name.lstrip("$").split("-"))

        merged = list(llm_suggestions)
        for s in static_suggestions:
            if s["skill"] in llm_skill_names:
                continue
            # Skip static skill if its name tokens overlap significantly with an LLM result
            static_tokens = set(s["skill"].lstrip("$").split("-"))
            overlap = static_tokens & llm_name_tokens
            if len(overlap) >= 2 and len(overlap) >= len(static_tokens) - 1:
                continue
            merged.append(s)
        suggestions = merged
    else:
        suggestions = static_suggestions

    # Try live discovery to check which suggested skills are actually installed
    live_skills = discover_skills_live()
    if live_skills:
        installed_names = {s["name"] for s in live_skills}
        for suggestion in suggestions:
            skill_name = suggestion["skill"].lstrip("$")
            suggestion["available"] = any(skill_name in name for name in installed_names)
    else:
        for suggestion in suggestions:
            suggestion["available"] = None  # Unknown

    return suggestions


def platform_supports_skills(backend_name: str) -> bool:
    """Check if a backend platform supports reusable skills."""
    return PLATFORM_SKILL_SUPPORT.get(backend_name.lower(), False)
