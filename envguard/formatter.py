"""Format .env file contents with consistent style."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FormatResult:
    original: Dict[str, str]
    formatted_lines: List[str] = field(default_factory=list)
    changes: int = 0

    @property
    def is_changed(self) -> bool:
        return self.changes > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "Already formatted, no changes needed."
        return f"{self.changes} line(s) reformatted."

    def to_string(self) -> str:
        return "\n".join(self.formatted_lines) + "\n"


def format_env(
    env: Dict[str, str],
    *,
    quote_values: bool = False,
    sort_keys: bool = False,
    original_lines: List[str] | None = None,
) -> FormatResult:
    """Return a FormatResult with consistently styled lines."""
    keys = sorted(env.keys()) if sort_keys else list(env.keys())
    formatted: List[str] = []
    for key in keys:
        value = env[key]
        if quote_values and not (value.startswith('"') and value.endswith('"')):
            value = f'"{value}"'
        formatted.append(f"{key}={value}")

    changes = 0
    if original_lines is not None:
        orig = [l.rstrip("\n") for l in original_lines if l.strip() and not l.startswith("#")]
        changes = sum(1 for a, b in zip(orig, formatted) if a != b)
        changes += abs(len(orig) - len(formatted))

    return FormatResult(original=env, formatted_lines=formatted, changes=changes)
