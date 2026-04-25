"""Type coercion for .env values — converts string values to inferred Python types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_TRUE_VALUES = {"true", "yes", "1", "on"}
_FALSE_VALUES = {"false", "no", "0", "off"}


def _coerce_value(raw: str) -> Any:
    """Return the most specific Python type for *raw*."""
    if raw.lower() in _TRUE_VALUES:
        return True
    if raw.lower() in _FALSE_VALUES:
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


@dataclass
class CoerceResult:
    coerced: Dict[str, Any] = field(default_factory=dict)
    type_map: Dict[str, str] = field(default_factory=dict)

    @property
    def change_count(self) -> int:
        """Number of keys whose type changed away from *str*."""
        return sum(1 for t in self.type_map.values() if t != "str")

    @property
    def is_changed(self) -> bool:
        return self.change_count > 0

    def summary(self) -> str:
        total = len(self.coerced)
        changed = self.change_count
        return f"{changed}/{total} value(s) coerced to non-string types."

    def to_string(self) -> str:
        lines: List[str] = []
        for key, value in sorted(self.coerced.items()):
            type_name = self.type_map[key]
            lines.append(f"{key}={value!r}  # {type_name}")
        return "\n".join(lines)


def coerce_env(env: Dict[str, str]) -> CoerceResult:
    """Coerce all string values in *env* to their inferred Python types."""
    coerced: Dict[str, Any] = {}
    type_map: Dict[str, str] = {}
    for key, raw in env.items():
        value = _coerce_value(raw)
        coerced[key] = value
        type_map[key] = type(value).__name__
    return CoerceResult(coerced=coerced, type_map=type_map)
