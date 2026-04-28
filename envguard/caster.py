"""caster.py – cast env values to explicit target types.

Supports casting to: str, int, float, bool, list (comma-separated).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _cast(value: str, target: str) -> Tuple[Any, bool]:
    """Return (cast_value, changed).  Raises ValueError on bad input."""
    t = target.lower()
    if t == "str":
        return value, False
    if t == "int":
        casted = int(value)
        return casted, str(casted) != value
    if t == "float":
        casted = float(value)
        return casted, str(casted) != value
    if t == "bool":
        low = value.strip().lower()
        if low in _BOOL_TRUE:
            return True, value != "True"
        if low in _BOOL_FALSE:
            return False, value != "False"
        raise ValueError(f"Cannot cast {value!r} to bool")
    if t == "list":
        items = [v.strip() for v in value.split(",") if v.strip()]
        return items, True
    raise ValueError(f"Unknown target type: {target!r}")


@dataclass
class CastResult:
    env: Dict[str, Any]
    changed_keys: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def change_count(self) -> int:
        return len(self.changed_keys)

    @property
    def is_changed(self) -> bool:
        return bool(self.changed_keys)

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        parts = [f"{len(self.env)} key(s)"]
        if self.change_count:
            parts.append(f"{self.change_count} cast")
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        return ", ".join(parts)


def cast_env(
    env: Dict[str, str],
    casts: Dict[str, str],
) -> CastResult:
    """Apply *casts* mapping of key→type to *env*.

    Keys not listed in *casts* are kept as-is (str).
    Invalid casts are recorded in ``errors`` and the original str value is kept.
    """
    result: Dict[str, Any] = dict(env)
    changed: List[str] = []
    errors: Dict[str, str] = {}

    for key, target in casts.items():
        if key not in env:
            continue
        try:
            casted, did_change = _cast(env[key], target)
            result[key] = casted
            if did_change:
                changed.append(key)
        except (ValueError, TypeError) as exc:
            errors[key] = str(exc)

    return CastResult(env=result, changed_keys=sorted(changed), errors=errors)
