"""Resolve environment variable references across multiple .env files.

Given an ordered list of env dicts (base → override), produce a fully
resolved flat dict where each value has had its ${VAR} / $VAR references
expanded using the merged context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class ResolveResult:
    resolved: Dict[str, str]
    unresolved_refs: Dict[str, List[str]] = field(default_factory=dict)  # key -> missing var names

    @property
    def is_clean(self) -> bool:
        return len(self.unresolved_refs) == 0

    @property
    def total_keys(self) -> int:
        return len(self.resolved)

    def summary(self) -> str:
        if self.is_clean:
            return f"Resolved {self.total_keys} keys with no unresolved references."
        missing = sum(len(v) for v in self.unresolved_refs.values())
        return (
            f"Resolved {self.total_keys} keys; "
            f"{len(self.unresolved_refs)} key(s) have {missing} unresolved reference(s)."
        )


def _merge_layers(layers: List[Dict[str, str]]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for layer in layers:
        merged.update(layer)
    return merged


def _expand(value: str, context: Dict[str, str]) -> tuple[str, List[str]]:
    """Expand all ${VAR}/$VAR references in *value* using *context*.

    Returns (expanded_value, list_of_missing_var_names).
    """
    missing: List[str] = []

    def replacer(m: re.Match) -> str:
        var = m.group(1) or m.group(2)
        if var in context:
            return context[var]
        missing.append(var)
        return m.group(0)  # leave original token intact

    expanded = _REF_RE.sub(replacer, value)
    return expanded, missing


def resolve_envs(layers: List[Dict[str, str]]) -> ResolveResult:
    """Merge *layers* in order and expand variable references.

    Earlier layers are the base; later layers override.  References are
    resolved against the fully-merged context so any layer may reference
    a variable defined in any other layer.
    """
    context = _merge_layers(layers)
    resolved: Dict[str, str] = {}
    unresolved_refs: Dict[str, List[str]] = {}

    for key, raw_value in context.items():
        expanded, missing = _expand(raw_value, context)
        resolved[key] = expanded
        if missing:
            unresolved_refs[key] = missing

    return ResolveResult(resolved=resolved, unresolved_refs=unresolved_refs)
