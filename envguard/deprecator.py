"""Detect deprecated keys in .env files based on a deprecation map."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DeprecationIssue:
    key: str
    replacement: Optional[str] = None

    def __str__(self) -> str:
        msg = f"Deprecated key: {self.key}"
        if self.replacement:
            msg += f" (use '{self.replacement}' instead)"
        return msg


@dataclass
class DeprecationResult:
    issues: List[DeprecationIssue] = field(default_factory=list)
    checked: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def summary(self) -> str:
        if self.is_clean:
            return f"No deprecated keys found ({self.checked} keys checked)."
        return (
            f"{self.issue_count} deprecated key(s) found "
            f"out of {self.checked} checked."
        )


def check_deprecations(
    env: Dict[str, str],
    deprecation_map: Dict[str, Optional[str]],
) -> DeprecationResult:
    """Check env keys against a deprecation map.

    Args:
        env: parsed env dict.
        deprecation_map: mapping of deprecated_key -> replacement (or None).
    """
    issues: List[DeprecationIssue] = []
    for key in env:
        if key in deprecation_map:
            issues.append(DeprecationIssue(key=key, replacement=deprecation_map[key]))
    return DeprecationResult(issues=issues, checked=len(env))
