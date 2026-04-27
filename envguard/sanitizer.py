"""Sanitize .env values by applying configurable cleaning rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

_CTRL_CHARS = {chr(i) for i in range(32) if i not in (9, 10, 13)}


def _strip_ctrl(value: str) -> str:
    return "".join(c for c in value if c not in _CTRL_CHARS)


def _strip_null(value: str) -> str:
    return value.replace("\x00", "")


def _collapse_spaces(value: str) -> str:
    import re
    return re.sub(r" {2,}", " ", value)


@dataclass
class SanitizeResult:
    original: Dict[str, str]
    sanitized: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.changed_keys)

    @property
    def is_changed(self) -> bool:
        return bool(self.changed_keys)

    def summary(self) -> str:
        if not self.is_changed:
            return "All values are clean — no sanitization needed."
        keys = ", ".join(self.changed_keys)
        return f"Sanitized {self.change_count} value(s): {keys}"

    def to_string(self) -> str:
        lines = []
        for key, value in self.sanitized.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)


def sanitize_env(
    env: Dict[str, str],
    *,
    strip_ctrl: bool = True,
    strip_null: bool = True,
    collapse_spaces: bool = False,
) -> SanitizeResult:
    """Return a SanitizeResult with cleaned values."""
    sanitized: Dict[str, str] = {}
    changed: List[str] = []

    for key, value in env.items():
        new_val = value
        if strip_null:
            new_val = _strip_null(new_val)
        if strip_ctrl:
            new_val = _strip_ctrl(new_val)
        if collapse_spaces:
            new_val = _collapse_spaces(new_val)
        sanitized[key] = new_val
        if new_val != value:
            changed.append(key)

    return SanitizeResult(original=dict(env), sanitized=sanitized, changed_keys=changed)
