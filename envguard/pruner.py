"""pruner.py — remove keys from a .env mapping by name or pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class PruneResult:
    """Result of a prune operation."""
    original: Dict[str, str]
    pruned: Dict[str, str]          # keys that were removed  {key: old_value}
    result: Dict[str, str]          # surviving env after pruning

    # --- convenience properties ---

    @property
    def prune_count(self) -> int:
        """Number of keys removed."""
        return len(self.pruned)

    @property
    def is_changed(self) -> bool:
        """True when at least one key was removed."""
        return self.prune_count > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "No keys pruned."
        keys = ", ".join(sorted(self.pruned))
        return f"Pruned {self.prune_count} key(s): {keys}"

    def to_string(self) -> str:
        """Serialise *result* back to .env format."""
        lines = [f"{k}={v}" for k, v in sorted(self.result.items())]
        return "\n".join(lines) + ("\n" if lines else "")


def prune_env(
    env: Dict[str, str],
    keys: Sequence[str] = (),
    patterns: Sequence[str] = (),
) -> PruneResult:
    """Remove *keys* and any key matching a regex in *patterns* from *env*.

    Parameters
    ----------
    env:      Parsed env mapping.
    keys:     Exact key names to remove.
    patterns: Regular-expression strings; any key that fully matches one of
              these patterns is also removed.
    """
    compiled = [re.compile(p) for p in patterns]
    exact = set(keys)

    pruned: Dict[str, str] = {}
    result: Dict[str, str] = {}

    for k, v in env.items():
        removed = k in exact or any(rx.fullmatch(k) for rx in compiled)
        if removed:
            pruned[k] = v
        else:
            result[k] = v

    return PruneResult(original=dict(env), pruned=pruned, result=result)
