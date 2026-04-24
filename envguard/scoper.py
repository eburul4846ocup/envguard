"""Scope filtering: extract a subset of env vars by prefix or key list."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeResult:
    scoped: Dict[str, str]
    excluded: Dict[str, str]
    prefix: Optional[str]
    keys: List[str]

    @property
    def key_count(self) -> int:
        return len(self.scoped)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    def summary(self) -> str:
        parts = [f"scoped={self.key_count}", f"excluded={self.excluded_count}"]
        if self.prefix:
            parts.append(f"prefix={self.prefix!r}")
        if self.keys:
            parts.append(f"keys={len(self.keys)}")
        return "ScopeResult(" + ", ".join(parts) + ")"

    def to_string(self, strip_prefix: bool = False) -> str:
        """Render scoped vars as .env lines, optionally stripping the prefix."""
        lines: List[str] = []
        for k, v in sorted(self.scoped.items()):
            key = k
            if strip_prefix and self.prefix and k.startswith(self.prefix):
                key = k[len(self.prefix):]
            lines.append(f"{key}={v}")
        return "\n".join(lines)


def scope_env(
    env: Dict[str, str],
    *,
    prefix: Optional[str] = None,
    keys: Optional[List[str]] = None,
    case_sensitive: bool = True,
) -> ScopeResult:
    """Return a ScopeResult containing only matching keys.

    If *prefix* is given, include keys that start with it.
    If *keys* is given, include only those exact keys.
    Both filters may be combined (union).
    """
    if not prefix and not keys:
        return ScopeResult(
            scoped=dict(env),
            excluded={},
            prefix=prefix,
            keys=keys or [],
        )

    wanted: set = set()

    if prefix:
        p = prefix if case_sensitive else prefix.upper()
        for k in env:
            cmp = k if case_sensitive else k.upper()
            if cmp.startswith(p):
                wanted.add(k)

    if keys:
        for k in keys:
            if not case_sensitive:
                for ek in env:
                    if ek.upper() == k.upper():
                        wanted.add(ek)
            elif k in env:
                wanted.add(k)

    scoped = {k: env[k] for k in env if k in wanted}
    excluded = {k: env[k] for k in env if k not in wanted}

    return ScopeResult(
        scoped=scoped,
        excluded=excluded,
        prefix=prefix,
        keys=list(keys or []),
    )
