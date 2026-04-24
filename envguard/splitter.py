"""Split a single .env file into multiple files grouped by key prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SplitResult:
    """Result of splitting an env dict into prefix-based groups."""

    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    @property
    def total_keys(self) -> int:
        total = sum(len(v) for v in self.groups.values())
        return total + len(self.ungrouped)

    @property
    def file_count(self) -> int:
        """Number of output files that would be written (groups + ungrouped if non-empty)."""
        return len(self.groups) + (1 if self.ungrouped else 0)

    def summary(self) -> str:
        parts = [f"{name}: {len(keys)} key(s)" for name, keys in sorted(self.groups.items())]
        if self.ungrouped:
            parts.append(f"ungrouped: {len(self.ungrouped)} key(s)")
        return ", ".join(parts) if parts else "no keys"


def split_env(
    env: Dict[str, str],
    separator: str = "_",
    prefixes: Optional[List[str]] = None,
) -> SplitResult:
    """Split *env* into groups by key prefix.

    If *prefixes* is given, only those prefixes are used as group names.
    Otherwise every key's first segment (before *separator*) becomes a group
    provided at least two keys share that prefix; lone keys fall into
    ``ungrouped``.
    """
    result = SplitResult()

    if prefixes is not None:
        explicit = {p.upper() for p in prefixes}
        for key, value in env.items():
            matched = next(
                (p for p in explicit if key.upper().startswith(p + separator.upper())),
                None,
            )
            if matched:
                result.groups.setdefault(matched, {})[key] = value
            else:
                result.ungrouped[key] = value
        return result

    # Auto-detect prefixes: group by first segment when shared by ≥2 keys.
    prefix_map: Dict[str, List[str]] = {}
    for key in env:
        if separator in key:
            prefix = key.split(separator, 1)[0]
        else:
            prefix = ""
        prefix_map.setdefault(prefix, []).append(key)

    for prefix, keys in prefix_map.items():
        if prefix and len(keys) >= 2:
            for k in keys:
                result.groups.setdefault(prefix, {})[k] = env[k]
        else:
            for k in keys:
                result.ungrouped[k] = env[k]

    return result


def write_split(
    result: SplitResult,
    output_dir: Path,
    ungrouped_name: str = ".env.misc",
) -> List[Path]:
    """Write each group to *output_dir* as ``.<group_name>.env`` (lower-cased).

    Returns the list of paths written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    for group_name, pairs in sorted(result.groups.items()):
        path = output_dir / f".env.{group_name.lower()}"
        lines = [f"{k}={v}" for k, v in sorted(pairs.items())]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)

    if result.ungrouped:
        path = output_dir / ungrouped_name
        lines = [f"{k}={v}" for k, v in sorted(result.ungrouped.items())]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)

    return written
