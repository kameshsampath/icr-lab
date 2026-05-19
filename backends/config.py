"""Configuration loader for ICR Lab.

Reads and writes icr-lab.toml with section ownership semantics.
Sections are owned by specific modules/skills:
  - [icr-lab.backend] / [icr-lab.backend.*]: backends module, scaffold-backend skill
  - [icr-lab.deploy]: deploy-sis skill
"""

import os
import logging
import subprocess
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11 fallback

logger = logging.getLogger(__name__)

_CONFIG_FILE = "icr-lab.toml"

_SCHEMA_NAME = "icr-lab"
_SCHEMA_VERSION = "0.2.0"

_DEFAULT_CONFIG_TEMPLATE = """\
_schema = "icr-lab"
_version = "0.2.0"

# ICR Lab Configuration
# Section ownership: [icr-lab.backend*] = backends module + scaffold-backend skill
#                    [icr-lab.deploy]    = deploy-sis skill

[icr-lab.backend]
default = "simulation"

[icr-lab.backend.simulation]
# Always available — deterministic engine, no external deps

[icr-lab.backend.cortex]
model = "llama3.1-8b"
connection = "{connection}"
database = "{prefix}_ICR_LAB"
schema = "PUBLIC"

[icr-lab.deploy]
database = "{prefix}_ICR_LAB"
schema = "PUBLIC"
warehouse = "{warehouse}"
compute_pool = ""
connection = "{connection}"
"""


def _get_snowflake_connection_info() -> dict:
    """Resolve Snowflake connection details for config defaults.

    Returns a dict with keys: user, connection, warehouse, database, role.
    Sources (in priority order):
    1. Environment variables (SNOWFLAKE_USER, etc.)
    2. `snow connection test --format json` output
    3. OS username / empty strings as fallback
    """
    info = {
        "user": "",
        "connection": "default",
        "warehouse": "",
        "database": "",
        "role": "",
    }

    # Try snow connection test first (gives us the most fields)
    try:
        result = subprocess.run(
            ["snow", "connection", "test", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            info["user"] = data.get("User", "") or ""
            conn_name = data.get("Connection name", "") or ""
            if conn_name:
                info["connection"] = conn_name
            wh = data.get("Warehouse", "") or ""
            if wh and wh != "not set":
                info["warehouse"] = wh
            db = data.get("Database", "") or ""
            if db and db != "not set":
                info["database"] = db
            role = data.get("Role", "") or ""
            if role and role != "not set":
                info["role"] = role
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug("snow connection test failed: %s", e)

    # Env vars override
    env_user = os.environ.get("SNOWFLAKE_USER", "")
    if env_user:
        info["user"] = env_user

    # Final fallback for user
    if not info["user"]:
        info["user"] = os.environ.get("USER", "user")

    info["user"] = info["user"].upper()
    return info


def _get_snowflake_user() -> str:
    """Resolve the Snowflake username for config defaults.

    Convenience wrapper around _get_snowflake_connection_info().
    """
    return _get_snowflake_connection_info()["user"]


def _render_default_config() -> str:
    """Render the default config template with connection info."""
    info = _get_snowflake_connection_info()
    return _DEFAULT_CONFIG_TEMPLATE.format(
        prefix=info["user"],
        connection=info["connection"],
        warehouse=info["warehouse"],
    )


def _find_config() -> Path:
    """Find icr-lab.toml starting from CWD, walking up to project root."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / _CONFIG_FILE
        if candidate.exists():
            return candidate
        # Stop at project root markers
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent / _CONFIG_FILE
    return current / _CONFIG_FILE


def load_config() -> dict:
    """Load the icr-lab.toml config file.

    Returns:
        Parsed TOML as a flat-ish dict. Nested tables like [icr-lab.backend.cortex]
        are returned as top-level keys "backend.cortex" -> dict.
        The [icr-lab.deploy] section is returned as "deploy" -> dict.
    """
    path = _find_config()
    if not path.exists():
        return {"backend": {"default": "simulation"}}

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    # The icr-lab namespace is the top-level container
    icr = raw.get("icr-lab", {})

    # Flatten nested backend sections for easy lookup
    result = {}
    backend = icr.get("backend", {})
    if isinstance(backend, dict):
        result["backend"] = {"default": backend.get("default", "simulation")}
        for sub_key, sub_value in backend.items():
            if isinstance(sub_value, dict):
                result[f"backend.{sub_key}"] = sub_value

    # Include deploy section
    deploy = icr.get("deploy", {})
    if isinstance(deploy, dict):
        result["deploy"] = deploy

    # Preserve top-level scalars (_schema, _version)
    for key, value in raw.items():
        if key != "icr-lab" and not isinstance(value, dict):
            result[key] = value

    return result


def save_backend_section(name: str, settings: dict) -> None:
    """Add or update a [icr-lab.backend.<name>] section in icr-lab.toml.

    This respects section ownership — only touches backend sections.

    Args:
        name: Backend name (e.g., "cortex", "lmstudio")
        settings: Dict of settings for this backend.
    """
    path = _find_config()

    if path.exists():
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    else:
        raw = {"_schema": _SCHEMA_NAME, "_version": _SCHEMA_VERSION, "icr-lab": {"backend": {"default": "simulation"}}}

    if "icr-lab" not in raw:
        raw["icr-lab"] = {"backend": {"default": "simulation"}}
    if "backend" not in raw["icr-lab"]:
        raw["icr-lab"]["backend"] = {"default": "simulation"}

    raw["icr-lab"]["backend"][name] = settings

    # Write back as TOML (manual serialization since tomllib is read-only)
    _write_toml(path, raw)


def _write_toml(path: Path, data: dict) -> None:
    """Write a dict as TOML to a file.

    Handles up to 3 levels of nesting (e.g. [icr-lab.backend.cortex]).
    """
    lines = []
    # Write top-level scalars first
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_toml_value(value)}")

    if lines:
        lines.append("")

    # Write sections (recursive up to 3 levels)
    def _write_section(prefix: str, table: dict):
        scalars = [(k, v) for k, v in table.items() if not isinstance(v, dict)]
        subtables = [(k, v) for k, v in table.items() if isinstance(v, dict)]

        if scalars:
            lines.append(f"[{prefix}]")
            for k, v in scalars:
                lines.append(f"{k} = {_toml_value(v)}")
            lines.append("")

        for sub_key, sub_value in subtables:
            _write_section(f"{prefix}.{sub_key}", sub_value)

    for key, value in data.items():
        if isinstance(value, dict):
            _write_section(key, value)

    path.write_text("\n".join(lines) + "\n")


def _toml_value(value) -> str:
    """Convert a Python value to TOML representation."""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, list):
        items = ", ".join(_toml_value(v) for v in value)
        return f"[{items}]"
    return f'"{value}"'


def validate_config() -> tuple[bool, list[str]]:
    """Validate icr-lab.toml structure.

    Checks: parseable, _schema == 'icr-lab', [icr-lab.backend] exists,
    default key points to a defined [icr-lab.backend.*], at least one backend section.
    Returns (valid, issues).
    """
    path = _find_config()
    issues: list[str] = []

    if not path.exists():
        return False, ["icr-lab.toml not found"]

    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except Exception as e:
        return False, [f"Parse error: {e}"]

    # Check schema marker
    if raw.get("_schema") != _SCHEMA_NAME:
        issues.append(f"Missing or wrong _schema (expected '{_SCHEMA_NAME}')")

    # Check icr-lab namespace
    icr = raw.get("icr-lab")
    if not icr or not isinstance(icr, dict):
        issues.append("Missing [icr-lab] namespace")
        return (False, issues)

    # Check backend section
    backend = icr.get("backend")
    if backend is None:
        issues.append("Missing [icr-lab.backend] section")
    elif not isinstance(backend, dict):
        issues.append("[icr-lab.backend] is not a table")
    else:
        default = backend.get("default", "")
        # Check at least one backend subsection
        subsections = [k for k, v in backend.items() if isinstance(v, dict)]
        if not subsections:
            issues.append("No backend subsections defined (e.g., [icr-lab.backend.simulation])")
        elif default and default not in subsections:
            issues.append(f"default '{default}' does not match any [icr-lab.backend.*] section")

    return (len(issues) == 0, issues)


def ensure_config(force: bool = False) -> Path:
    """Ensure icr-lab.toml exists and is valid.

    - Missing -> write _render_default_config() (with user prefix)
    - Corrupted (parse fails) -> backup .bak, write fresh
    - Wrong schema -> backup .bak, write fresh (with warning)
    - force=True -> unconditional overwrite (clean reset)
    Returns path to the config file.
    """
    path = _find_config()

    if force:
        if path.exists():
            path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_render_default_config())
        return path

    if not path.exists():
        path.write_text(_render_default_config())
        return path

    # Try to parse
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except Exception:
        # Corrupted — backup and rewrite
        path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_render_default_config())
        return path

    # Check schema ownership
    if raw.get("_schema") != _SCHEMA_NAME:
        path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_render_default_config())

    return path
