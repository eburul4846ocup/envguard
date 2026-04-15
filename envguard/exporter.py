"""Export parsed .env data to various formats (shell, JSON, YAML)."""

from __future__ import annotations

import json
from enum import Enum
from typing import Dict


class ExportFormat(str, Enum):
    SHELL = "shell"
    JSON = "json"
    DOTENV = "dotenv"


def export_shell(env: Dict[str, str]) -> str:
    """Export env vars as shell export statements."""
    lines = []
    for key, value in sorted(env.items()):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_json(env: Dict[str, str]) -> str:
    """Export env vars as a JSON object."""
    return json.dumps(dict(sorted(env.items())), indent=2) + "\n"


def export_dotenv(env: Dict[str, str]) -> str:
    """Export env vars in canonical .env format."""
    lines = []
    for key, value in sorted(env.items()):
        if any(c in value for c in (" ", "\t", '"', "'", "#", "=")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def export_env(
    env: Dict[str, str],
    fmt: ExportFormat = ExportFormat.DOTENV,
) -> str:
    """Dispatch to the appropriate exporter based on *fmt*."""
    if fmt == ExportFormat.SHELL:
        return export_shell(env)
    if fmt == ExportFormat.JSON:
        return export_json(env)
    return export_dotenv(env)
