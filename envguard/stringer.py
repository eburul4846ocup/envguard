"""envguard.stringer – stringify an env dict to various formats."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class StringifyResult:
    """Result of stringifying an env mapping."""

    lines: List[str] = field(default_factory=list)
    key_count: int = 0
    format: str = "dotenv"

    def is_empty(self) -> bool:
        return self.key_count == 0

    def summary(self) -> str:
        return f"Stringified {self.key_count} key(s) as '{self.format}' format."

    def to_string(self) -> str:
        return "\n".join(self.lines)


def _quote_if_needed(value: str) -> str:
    """Wrap value in double quotes if it contains spaces or special chars."""
    if any(c in value for c in (" ", "\t", "#", "'", '"', "$", "\\`")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value


def stringify_env(
    env: Dict[str, str],
    *,
    quote_values: bool = False,
    sort_keys: bool = True,
    fmt: str = "dotenv",
    separator: str = "=",
) -> StringifyResult:
    """Convert an env mapping to a list of formatted lines.

    Args:
        env: Mapping of key -> value.
        quote_values: Always wrap values in double quotes.
        sort_keys: Emit keys in alphabetical order.
        fmt: Output format label stored on the result (informational).
        separator: Character(s) between key and value.

    Returns:
        StringifyResult with rendered lines.
    """
    keys = sorted(env.keys()) if sort_keys else list(env.keys())
    lines: List[str] = []
    for key in keys:
        value = env[key]
        if quote_values:
            escaped = value.replace('"', '\\"')
            rendered = f'"{escaped}"'
        else:
            rendered = _quote_if_needed(value)
        lines.append(f"{key}{separator}{rendered}")

    return StringifyResult(lines=lines, key_count=len(keys), format=fmt)
