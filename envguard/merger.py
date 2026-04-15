"""Merge multiple .env files with conflict detection and resolution strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class MergeStrategy(str, Enum):
    FIRST_WINS = "first-wins"   # first file defining a key wins
    LAST_WINS = "last-wins"     # last file defining a key wins
    STRICT = "strict"           # raise on any conflict


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_path, value)

    def __str__(self) -> str:
        sources = ", ".join(f"{p}={v!r}" for p, v in self.values)
        return f"Conflict on '{self.key}': {sources}"


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


class MergeError(ValueError):
    """Raised when STRICT strategy encounters a conflict."""


def merge_envs(
    sources: List[Tuple[str, Dict[str, str]]],
    strategy: MergeStrategy = MergeStrategy.LAST_WINS,
) -> MergeResult:
    """Merge a list of (path, env_dict) pairs into a single MergeResult.

    Args:
        sources: Ordered list of (source_label, key-value mapping) tuples.
        strategy: How to handle conflicting keys.

    Returns:
        MergeResult with merged dict and any detected conflicts.

    Raises:
        MergeError: When strategy is STRICT and a conflict is detected.
    """
    merged: Dict[str, str] = {}
    conflict_map: Dict[str, List[Tuple[str, str]]] = {}

    for path, env in sources:
        for key, value in env.items():
            if key in merged and merged[key] != value:
                conflict_map.setdefault(key, [(path, merged[key])])
                # avoid duplicate source entries
                existing_paths = {p for p, _ in conflict_map[key]}
                if path not in existing_paths:
                    conflict_map[key].append((path, value))

                if strategy == MergeStrategy.STRICT:
                    raise MergeError(
                        f"Conflict on key '{key}': already defined with a different value."
                    )
                if strategy == MergeStrategy.LAST_WINS:
                    merged[key] = value
                # FIRST_WINS: keep existing value, do nothing
            else:
                merged[key] = value
                if key not in conflict_map:
                    pass  # no conflict yet

    conflicts = [
        MergeConflict(key=k, values=v) for k, v in conflict_map.items()
    ]
    return MergeResult(merged=merged, conflicts=conflicts)
