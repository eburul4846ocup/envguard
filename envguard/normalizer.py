"""Normalize .env variable values (trim whitespace, unify quotes, etc.)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class NormalizeResult:
    normalized: Dict[str, str]
    changes: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old, new)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def is_changed(self) -> bool:
        return bool(self.changes)

    def summary(self) -> str:
        if not self.is_changed:
            return "No normalization changes."
        lines = [f"{self.change_count} value(s) normalized:"]
        for key, old, new in self.changes:
            lines.append(f"  {key}: {old!r} -> {new!r}")
        return "\n".join(lines)

    def to_string(self) -> str:
        """Render normalized env as .env file content."""
        return "\n".join(f"{k}={v}" for k, v in sorted(self.normalized.items())) + "\n"


def _normalize_value(value: str, strip_quotes: bool, lowercase_booleans: bool) -> str:
    value = value.strip()
    if strip_quotes and len(value) >= 2:
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
    if lowercase_booleans and value.lower() in {true", "false",()
    return value
n    env: Dict[str, str],
,
    strip_quotes: bool = True,
    lowercase_booleans: bool = True,
) -> NormalizeResult:
    normalized: Dict[str, str] = {}
    changes: List[Tuple[str, str, str]] = []
    for key, original in env.items():
        new_val = _normalize_value(original, strip_quotes, lowercase_booleans)
        normalized[key] = new_val
        if new_val != original:
            changes.append((key, original, new_val))
    return NormalizeResult(normalized=normalized, changes=changes)
