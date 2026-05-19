"""Configuration loader for ICR Lab.

Reads and writes icr-lab.toml with section ownership semantics.
Sections are owned by specific modules/skills:
  - [backend] / [backend.*]: backends module, scaffold-backend skill
  - [deploy]: deploy-sis skill
"""

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11 fallback

_CONFIG_FILE = "icr-lab.toml"

_SCHEMA_NAME = "icr-lab"
_SCHEMA_VERSION = "0.2.0"

_DEFAULT_CONFIG = """\
_schema = "icr-lab"
_version = "0.2.0"

# ICR Lab Configuration
# Section ownership: [backend*] = backends module + scaffold-backend skill
#                    [deploy]   = deploy-sis skill

[backend]
default = "simulation"

[backend.simulation]
# Always available — deterministic engine, no external deps

[backend.cortex]
model = "llama3.1-8b"
connection = "default"
database = ""
schema = ""

[deploy]
database = ""
schema = ""
warehouse = ""
compute_pool = ""
connection = ""
"""


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
        Parsed TOML as a flat-ish dict. Nested tables like [backend.cortex]
        are returned as top-level keys "backend.cortex" -> dict.
    """
    path = _find_config()
    if not path.exists():
        return {"backend": {"default": "simulation"}}

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    # Flatten nested backend sections for easy lookup
    result = {}
    for key, value in raw.items():
        if key == "backend" and isinstance(value, dict):
            # Extract default and nested backend configs
            result["backend"] = {"default": value.get("default", "simulation")}
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    result[f"backend.{sub_key}"] = sub_value
        else:
            result[key] = value
    return result


def save_backend_section(name: str, settings: dict) -> None:
    """Add or update a [backend.<name>] section in icr-lab.toml.

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
        raw = {"backend": {"default": "simulation"}}

    if "backend" not in raw:
        raw["backend"] = {"default": "simulation"}

    raw["backend"][name] = settings

    # Write back as TOML (manual serialization since tomllib is read-only)
    _write_toml(path, raw)


def _write_toml(path: Path, data: dict) -> None:
    """Write a dict as TOML to a file."""
    lines = []
    # Write top-level scalars first
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_toml_value(value)}")

    if lines:
        lines.append("")

    # Write sections
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"[{key}]")
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    # Nested table
                    lines.append("")
                    lines.append(f"[{key}.{sub_key}]")
                    for k, v in sub_value.items():
                        lines.append(f"{k} = {_toml_value(v)}")
                else:
                    lines.append(f"{sub_key} = {_toml_value(sub_value)}")
            lines.append("")

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

    Checks: parseable, _schema == 'icr-lab', [backend] exists,
    default key points to a defined [backend.*], at least one backend section.
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

    # Check backend section
    if "backend" not in raw:
        issues.append("Missing [backend] section")
    elif not isinstance(raw["backend"], dict):
        issues.append("[backend] is not a table")
    else:
        backend = raw["backend"]
        default = backend.get("default", "")
        # Check at least one backend subsection
        subsections = [k for k, v in backend.items() if isinstance(v, dict)]
        if not subsections:
            issues.append("No backend subsections defined (e.g., [backend.simulation])")
        elif default and default not in subsections:
            issues.append(f"default '{default}' does not match any [backend.*] section")

    return (len(issues) == 0, issues)


def ensure_config(force: bool = False) -> Path:
    """Ensure icr-lab.toml exists and is valid.

    - Missing -> write _DEFAULT_CONFIG
    - Corrupted (parse fails) -> backup .bak, write fresh
    - Wrong schema -> backup .bak, write fresh (with warning)
    - force=True -> unconditional overwrite (clean reset)
    Returns path to the config file.
    """
    path = _find_config()

    if force:
        if path.exists():
            path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_DEFAULT_CONFIG)
        return path

    if not path.exists():
        path.write_text(_DEFAULT_CONFIG)
        return path

    # Try to parse
    try:
        with open(path, "rb") as f:
            raw = tomllib.load(f)
    except Exception:
        # Corrupted — backup and rewrite
        path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_DEFAULT_CONFIG)
        return path

    # Check schema ownership
    if raw.get("_schema") != _SCHEMA_NAME:
        path.rename(path.with_suffix(".toml.bak"))
        path.write_text(_DEFAULT_CONFIG)

    return path
