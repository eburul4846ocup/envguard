"""Diff two .env files and produce a human-readable / machine-readable diff."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envguard.parser import parse_env_file
from envguard.comparator import compare_envs, ComparisonResult


@dataclass
class DiffEntry:
    """A single line in the diff output."""
    key: str
    source_value: Optional[str]   # None  → key absent in source
    target_value: Optional[str]   # None  → key absent in target
    status: str                   # 'added' | 'removed' | 'changed' | 'unchanged'

    def __str__(self) -> str:  # pragma: no cover
        if self.status == "added":
            return f"+ {self.key}={self.target_value}"
        if self.status == "removed":
            return f"- {self.key}={self.source_value}"
        if self.status == "changed":
            return f"~ {self.key}: {self.source_value!r} → {self.target_value!r}"
        return f"  {self.key}={self.source_value}"


@dataclass
class EnvDiff:
    """Full diff result between two .env files."""
    source_path: str
    target_path: str
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(e.status != "unchanged" for e in self.entries)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "changed"]


def diff_env_files(
    source_path: str,
    target_path: str,
    ignore_values: bool = False,
) -> EnvDiff:
    """Parse both files and return an :class:`EnvDiff`."""
    source: Dict[str, str] = parse_env_file(source_path)
    target: Dict[str, str] = parse_env_file(target_path)

    result: ComparisonResult = compare_envs(source, target, ignore_values=ignore_values)

    all_keys = sorted(set(source) | set(target))
    entries: List[DiffEntry] = []

    for key in all_keys:
        if key in result.missing_in_target:
            entries.append(DiffEntry(key, source.get(key), None, "removed"))
        elif key in result.extra_in_target:
            entries.append(DiffEntry(key, None, target.get(key), "added"))
        elif key in result.value_mismatches:
            src_val, tgt_val = result.value_mismatches[key]
            entries.append(DiffEntry(key, src_val, tgt_val, "changed"))
        else:
            entries.append(DiffEntry(key, source.get(key), target.get(key), "unchanged"))

    return EnvDiff(source_path=source_path, target_path=target_path, entries=entries)
