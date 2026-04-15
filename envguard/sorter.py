"""Sort .env file keys alphabetically or by custom group order."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SortOrder(str, Enum):
    ALPHA = "alpha"
    ALPHA_DESC = "alpha_desc"
    LENGTH = "length"
    GROUP = "group"


@dataclass
class SortResult:
    original: Dict[str, str]
    sorted_env: Dict[str, str]
    order: SortOrder
    group_prefixes: List[str] = field(default_factory=list)

    @property
    def key_count(self) -> int:
        return len(self.sorted_env)

    def summary(self) -> str:
        return (
            f"Sorted {self.key_count} key(s) using order '{self.order.value}'."
        )


def _sort_by_group(
    env: Dict[str, str], prefixes: List[str]
) -> Dict[str, str]:
    """Sort keys so that known prefixes appear first, in prefix order."""
    buckets: Dict[str, List[str]] = {p: [] for p in prefixes}
    buckets["__other__"] = []

    for key in env:
        matched = False
        for prefix in prefixes:
            if key.startswith(prefix):
                buckets[prefix].append(key)
                matched = True
                break
        if not matched:
            buckets["__other__"].append(key)

    ordered: List[str] = []
    for prefix in prefixes:
        ordered.extend(sorted(buckets[prefix]))
    ordered.extend(sorted(buckets["__other__"]))

    return {k: env[k] for k in ordered}


def sort_env(
    env: Dict[str, str],
    order: SortOrder = SortOrder.ALPHA,
    group_prefixes: Optional[List[str]] = None,
) -> SortResult:
    """Return a SortResult with keys reordered according to *order*."""
    prefixes = group_prefixes or []

    if order == SortOrder.ALPHA:
        sorted_env = dict(sorted(env.items(), key=lambda kv: kv[0]))
    elif order == SortOrder.ALPHA_DESC:
        sorted_env = dict(sorted(env.items(), key=lambda kv: kv[0], reverse=True))
    elif order == SortOrder.LENGTH:
        sorted_env = dict(sorted(env.items(), key=lambda kv: len(kv[0])))
    elif order == SortOrder.GROUP:
        sorted_env = _sort_by_group(env, prefixes)
    else:
        sorted_env = dict(env)

    return SortResult(
        original=dict(env),
        sorted_env=sorted_env,
        order=order,
        group_prefixes=prefixes,
    )
