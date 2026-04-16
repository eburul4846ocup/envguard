"""Detect duplicate keys within a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class DuplicateResult:
    """Result of a duplicate-key scan on one .env file."""

    path: Path
    duplicates: Dict[str, List[int]] = field(default_factory=dict)
    # maps key -> list of 1-based line numbers where it appears (only keys
    # that appear MORE than once are included)

    @property
    def is_clean(self) -> bool:
        return len(self.duplicates) == 0

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicates)

    def summary(self) -> str:
        if self.is_clean:
            return f"{self.path}: no duplicate keys found."
        lines = [f"{self.path}: {self.duplicate_count} duplicate key(s) detected."]
        for key, occurrences in sorted(self.duplicates.items()):
            lines.append(f"  {key}: lines {', '.join(str(n) for n in occurrences)}")
        return "\n".join(lines)


def find_duplicates(path: Path) -> DuplicateResult:
    """Scan *path* for duplicate .env keys and return a :class:`DuplicateResult`.

    Comments (lines starting with ``#``) and blank lines are ignored.
    Only the raw key (before the first ``=``) is considered.
    """
    seen: Dict[str, List[int]] = {}

    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            if not key:
                continue
            seen.setdefault(key, []).append(lineno)

    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    return DuplicateResult(path=path, duplicates=duplicates)
