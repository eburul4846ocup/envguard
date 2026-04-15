"""Group .env keys by prefix or namespace for organized reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupResult:
    """Result of grouping env keys by prefix."""
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def group_names(self) -> List[str]:
        """Sorted list of group names."""
        return sorted(self.groups.keys())

    @property
    def total_keys(self) -> int:
        """Total number of keys across all groups and ungrouped."""
        return sum(len(v) for v in self.groups.values()) + len(self.ungrouped)

    def summary(self) -> str:
        lines = [f"Groups: {len(self.groups)}, Ungrouped: {len(self.ungrouped)}, Total: {self.total_keys}"]
        for name in self.group_names:
            lines.append(f"  [{name}] {len(self.groups[name])} key(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        return "\n".join(lines)


def group_env(
    env: Dict[str, str],
    separator: str = "_",
    min_prefix_length: int = 2,
    known_prefixes: Optional[List[str]] = None,
) -> GroupResult:
    """Group env variables by their key prefix.

    Args:
        env: Mapping of key -> value.
        separator: Character used to split prefix from the rest of the key.
        min_prefix_length: Minimum characters a prefix must have to be valid.
        known_prefixes: If provided, only group by these explicit prefixes.

    Returns:
        GroupResult with grouped and ungrouped keys.
    """
    groups: Dict[str, Dict[str, str]] = {}
    ungrouped: Dict[str, str] = {}

    for key, value in env.items():
        prefix = _extract_prefix(key, separator, min_prefix_length, known_prefixes)
        if prefix:
            groups.setdefault(prefix, {})[key] = value
        else:
            ungrouped[key] = value

    return GroupResult(groups=groups, ungrouped=ungrouped)


def _extract_prefix(
    key: str,
    separator: str,
    min_prefix_length: int,
    known_prefixes: Optional[List[str]],
) -> Optional[str]:
    """Return the prefix of a key, or None if it cannot be grouped."""
    if known_prefixes is not None:
        for prefix in known_prefixes:
            if key.startswith(prefix.upper() + separator.upper()):
                return prefix.upper()
        return None

    if separator not in key:
        return None

    prefix = key.split(separator, 1)[0]
    if len(prefix) < min_prefix_length:
        return None
    return prefix
