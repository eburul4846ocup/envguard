"""Cascade multiple .env files, with later files overriding earlier ones.

Typical use-case: load a base .env, then overlay a .env.local so that
local overrides win while shared defaults are preserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple


@dataclass
class CascadeResult:
    """Result of cascading two or more env mappings."""

    merged: Dict[str, str]
    # key -> list of (source_index, value) showing the override chain
    provenance: Dict[str, List[Tuple[int, str]]] = field(default_factory=dict)

    @property
    def key_count(self) -> int:
        return len(self.merged)

    @property
    def overridden_keys(self) -> List[str]:
        """Keys that were overridden at least once."""
        return sorted(k for k, chain in self.provenance.items() if len(chain) > 1)

    def summary(self) -> str:
        total = self.key_count
        overridden = len(self.overridden_keys)
        return (
            f"{total} key(s) in final env; "
            f"{overridden} key(s) overridden across layers"
        )


def cascade_envs(layers: Sequence[Dict[str, str]]) -> CascadeResult:
    """Merge *layers* left-to-right; later layers override earlier ones.

    Parameters
    ----------
    layers:
        Ordered sequence of env dicts.  Index 0 is the base layer;
        the last element has the highest priority.

    Returns
    -------
    CascadeResult with the merged mapping and full provenance data.
    """
    if not layers:
        return CascadeResult(merged={}, provenance={})

    merged: Dict[str, str] = {}
    provenance: Dict[str, List[Tuple[int, str]]] = {}

    for idx, layer in enumerate(layers):
        for key, value in layer.items():
            merged[key] = value
            provenance.setdefault(key, []).append((idx, value))

    return CascadeResult(merged=merged, provenance=provenance)
