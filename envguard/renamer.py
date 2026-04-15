"""Rename keys across a parsed .env dictionary with optional dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class RenameResult:
    renamed: Dict[str, str] = field(default_factory=dict)   # new_key -> value
    skipped: List[str] = field(default_factory=list)        # old keys not found
    applied: List[Tuple[str, str]] = field(default_factory=list)  # (old, new)

    @property
    def rename_count(self) -> int:
        return len(self.applied)

    def summary(self) -> str:
        lines = [f"Renamed {self.rename_count} key(s)."]
        if self.skipped:
            lines.append(f"Skipped (not found): {', '.join(sorted(self.skipped))}")
        return "\n".join(lines)


def rename_env(
    env: Dict[str, str],
    mapping: Dict[str, str],
) -> RenameResult:
    """Return a new env dict with keys renamed according to *mapping*.

    Args:
        env:     Original key/value pairs.
        mapping: {old_key: new_key} rename pairs.

    Returns:
        RenameResult with the updated dict, applied renames, and skipped keys.
    """
    result_dict: Dict[str, str] = dict(env)
    applied: List[Tuple[str, str]] = []
    skipped: List[str] = []

    for old_key, new_key in mapping.items():
        if old_key not in result_dict:
            skipped.append(old_key)
            continue
        value = result_dict.pop(old_key)
        result_dict[new_key] = value
        applied.append((old_key, new_key))

    return RenameResult(renamed=result_dict, skipped=skipped, applied=applied)
