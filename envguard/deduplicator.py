"""Deduplicator: remove duplicate keys from an env mapping, keeping the last occurrence."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envguard.parser import parse_env_file


@dataclass
class DeduplicateResult:
    """Holds the deduplicated env and metadata about removed duplicates."""
    env: Dict[str, str]
    removed: Dict[str, List[str]]  # key -> list of values that were discarded

    @property
    def duplicate_count(self) -> int:
        """Total number of duplicate entries removed."""
        return sum(len(v) for v in self.removed.values())

    @property
    def is_clean(self) -> bool:
        return self.duplicate_count == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No duplicate keys found."
        keys = ", ".join(sorted(self.removed))
        return (
            f"{self.duplicate_count} duplicate(s) removed across "
            f"{len(self.removed)} key(s): {keys}"
        )


def deduplicate_env(path: Path) -> DeduplicateResult:
    """Parse *path* line-by-line, keeping the last value for each key.

    Unlike ``parse_env_file`` which silently keeps the last value, this
    function also records every discarded earlier value so callers can
    report or audit them.
    """
    raw_lines: List[tuple[str, str]] = []

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, _, value = stripped.partition("=""")
            key = key.strip()
            # Strip surrounding quotes from value
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            raw_lines.append((key, value))

    # Build ordered mapping; track duplicates
    seen: Dict[str, str] = {}
    removed: Dict[str, List[str]] = {}

    for key, value in raw_lines:
        if key in seen:
            removed.setdefault(key, []).append(seen[key])
        seen[key] = value

    return DeduplicateResult(env=seen, removed=removed)
