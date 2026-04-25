"""Filter .env variables by key pattern, prefix, or value condition."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FilterResult:
    matched: Dict[str, str]
    excluded: Dict[str, str]
    patterns: List[str] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    @property
    def is_empty(self) -> bool:
        return len(self.matched) == 0

    def summary(self) -> str:
        return (
            f"Matched {self.match_count} key(s), "
            f"excluded {self.excluded_count} key(s) "
            f"using {len(self.patterns)} pattern(s)."
        )


def filter_env(
    env: Dict[str, str],
    *,
    prefixes: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    exclude_empty: bool = False,
    invert: bool = False,
) -> FilterResult:
    """Return a FilterResult partitioning *env* into matched and excluded.

    Matching rules (applied with OR logic):
      - ``prefixes``: key starts with any given prefix (case-insensitive).
      - ``patterns``: key matches any given regex pattern.
      - ``exclude_empty``: exclude keys whose value is empty string.

    If *invert* is True the match set becomes the exclusion set.
    """
    compiled = [re.compile(p, re.IGNORECASE) for p in (patterns or [])]
    active_patterns = list(patterns or []) + [f"{p}*" for p in (prefixes or [])]

    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for key, value in env.items():
        hit = False
        if prefixes:
            hit = any(key.upper().startswith(p.upper()) for p in prefixes)
        if not hit and compiled:
            hit = any(rx.search(key) for rx in compiled)
        if not hit and not prefixes and not compiled:
            hit = True  # no filter criteria → match everything
        if exclude_empty and value == "":
            hit = False

        if invert:
            hit = not hit

        if hit:
            matched[key] = value
        else:
            excluded[key] = value

    return FilterResult(
        matched=matched,
        excluded=excluded,
        patterns=active_patterns,
    )
