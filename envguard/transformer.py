"""Key/value transformation utilities for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple


TransformFn = Callable[[str, str], Tuple[str, str]]


@dataclass
class TransformResult:
    data: Dict[str, str]
    changes: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old, new)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    @property
    def is_changed(self) -> bool:
        return bool(self.changes)

    def summary(self) -> str:
        if not self.is_changed:
            return "No transformations applied."
        return f"{self.change_count} value(s) transformed."


def _builtin(name: str) -> TransformFn:
    def _upper(k: str, v: str) -> Tuple[str, str]:
        return k, v.upper()

    def _lower(k: str, v: str) -> Tuple[str, str]:
        return k, v.lower()

    def _strip(k: str, v: str) -> Tuple[str, str]:
        return k, v.strip()

    def _key_upper(k: str, v: str) -> Tuple[str, str]:
        return k.upper(), v

    mapping = {
        "uppercase": _upper,
        "lowercase": _lower,
        "strip": _strip,
        "key_uppercase": _key_upper,
    }
    if name not in mapping:
        raise ValueError(f"Unknown built-in transform: {name!r}")
    return mapping[name]


def transform_env(
    env: Dict[str, str],
    transforms: List[str | TransformFn],
) -> TransformResult:
    """Apply a sequence of transforms to *env* and return a TransformResult."""
    data: Dict[str, str] = dict(env)
    changes: List[Tuple[str, str, str]] = []

    for t in transforms:
        fn: TransformFn = _builtin(t) if isinstance(t, str) else t
        new_data: Dict[str, str] = {}
        for k, v in data.items():
            nk, nv = fn(k, v)
            if nk != k or nv != v:
                changes.append((k, v, nv if nk == k else f"{nk}={nv}"))
            new_data[nk] = nv
        data = new_data

    return TransformResult(data=data, changes=changes)
