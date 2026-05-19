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
