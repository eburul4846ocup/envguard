"""Variable interpolation resolver for .env files.

Expands references like ${VAR} or $VAR within values using
already-defined keys (in order) or an optional base environment.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationResult:
    resolved: Dict[str, str]
    unresolved_refs: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.unresolved_refs) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "All variable references resolved successfully."
        refs = ", ".join(sorted(set(self.unresolved_refs)))
        return f"Unresolved variable references: {refs}"


def _expand_value(
    value: str,
    context: Dict[str, str],
    unresolved: List[str],
) -> str:
    """Replace all ${VAR} / $VAR occurrences in *value* from *context*."""

    def replacer(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        if var_name in context:
            return context[var_name]
        unresolved.append(var_name)
        return match.group(0)  # leave original token intact

    return _REF_RE.sub(replacer, value)


def interpolate(
    env: Dict[str, str],
    base: Optional[Dict[str, str]] = None,
) -> InterpolationResult:
    """Resolve variable references in *env*.

    Resolution order for each key (left-to-right priority):
    1. Keys defined *before* the current key in *env* (sequential expansion).
    2. Keys from *base* (e.g. the process environment).

    Parameters
    ----------
    env:
        Ordered mapping of key -> raw value (as parsed from a .env file).
    base:
        Optional fallback mapping (e.g. ``os.environ``).
    """
    base = base or {}
    context: Dict[str, str] = {**base}
    resolved: Dict[str, str] = {}
    unresolved_refs: List[str] = []

    for key, raw_value in env.items():
        expanded = _expand_value(raw_value, context, unresolved_refs)
        resolved[key] = expanded
        context[key] = expanded  # make available to subsequent keys

    return InterpolationResult(resolved=resolved, unresolved_refs=unresolved_refs)
