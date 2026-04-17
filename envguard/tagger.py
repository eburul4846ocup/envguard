"""Tag env keys with user-defined labels for categorisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class TagResult:
    tags: Dict[str, List[str]]          # tag -> list of keys
    untagged: List[str]                 # keys with no matching tag
    key_tags: Dict[str, List[str]]      # key -> list of tags (reverse map)

    @property
    def tag_names(self) -> List[str]:
        return sorted(self.tags.keys())

    @property
    def total_keys(self) -> int:
        return sum(len(v) for v in self.tags.values()) + len(self.untagged)

    def summary(self) -> str:
        parts = [f"{t}({len(self.tags[t])})" for t in self.tag_names]
        untagged = len(self.untagged)
        return f"tags=[{', '.join(parts)}] untagged={untagged}"


def tag_env(
    env: Dict[str, str],
    rules: Dict[str, List[str]],   # tag -> list of key prefixes/substrings
    match_mode: str = "prefix",    # "prefix" | "contains"
) -> TagResult:
    """Assign tags to env keys based on prefix or substring rules."""
    tags: Dict[str, List[str]] = {t: [] for t in rules}
    key_tags: Dict[str, List[str]] = {k: [] for k in env}

    for key in env:
        for tag, patterns in rules.items():
            for pat in patterns:
                if match_mode == "prefix" and key.upper().startswith(pat.upper()):
                    tags[tag].append(key)
                    key_tags[key].append(tag)
                    break
                elif match_mode == "contains" and pat.upper() in key.upper():
                    tags[tag].append(key)
                    key_tags[key].append(tag)
                    break

    tagged: Set[str] = {k for k, t in key_tags.items() if t}
    untagged = [k for k in env if k not in tagged]

    for tag in tags:
        tags[tag] = sorted(tags[tag])

    return TagResult(
        tags=tags,
        untagged=sorted(untagged),
        key_tags=key_tags,
    )
