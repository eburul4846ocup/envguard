"""trimmer.py – strip leading/trailing whitespace from .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TrimResult:
    """Outcome of trimming whitespace from env values."""

    original: Dict[str, str]
    trimmed: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)

    # --- convenience properties ---

    @property
    def change_count(self) -> int:
        return len(self.changed_keys)

    @property
    def is_changed(self) -> bool:
        return bool(self.changed_keys)

    def summary(self) -> str:
        if not self.is_changed:
            return "No values required trimming."
        keys = ", ".join(self.changed_keys)
        return f"{self.change_count} value(s) trimmed: {keys}"

    def to_string(self) -> str:
        """Render trimmed env as .env-formatted text (sorted keys)."""
        lines = [f"{k}={v}" for k, v in sorted(self.trimmed.items())]
        return "\n".join(lines) + ("\n" if lines else "")


def trim_env(env: Dict[str, str]) -> TrimResult:
    """Return a TrimResult with all values stripped of surrounding whitespace.

    Keys are never modified; only values are trimmed.
    """
    trimmed: Dict[str, str] = {}
    changed: List[str] = []

    for key, value in env.items():
        new_value = value.strip()
        trimmed[key] = new_value
        if new_value != value:
            changed.append(key)

    return TrimResult(original=dict(env), trimmed=trimmed, changed_keys=sorted(changed))
