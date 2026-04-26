"""Key rotation helpers: detect stale keys and suggest replacements."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional


_DEFAULT_MAX_AGE_DAYS = 90


@dataclass
class RotationIssue:
    key: str
    pinned_date: Optional[date]
    age_days: Optional[int]
    reason: str

    def __str__(self) -> str:
        age = f" (age {self.age_days}d)" if self.age_days is not None else ""
        return f"{self.key}{age}: {self.reason}"


@dataclass
class RotationResult:
    issues: List[RotationIssue] = field(default_factory=list)
    checked: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def summary(self) -> str:
        if self.is_clean:
            return f"All {self.checked} key(s) are within rotation policy."
        return (
            f"{self.issue_count} rotation issue(s) found "
            f"across {self.checked} checked key(s)."
        )


def _parse_date(value: str) -> Optional[date]:
    """Try to parse ISO date (YYYY-MM-DD) from a value string."""
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def rotate_env(
    env: Dict[str, str],
    pin_dates: Optional[Dict[str, str]] = None,
    max_age_days: int = _DEFAULT_MAX_AGE_DAYS,
    secret_suffixes: tuple = ("SECRET", "KEY", "TOKEN", "PASSWORD", "PASS", "PWD"),
    today: Optional[date] = None,
) -> RotationResult:
    """Check secret keys against pin dates and flag stale or undated secrets."""
    today = today or date.today()
    pin_dates = pin_dates or {}
    result = RotationResult()

    for key in env:
        upper = key.upper()
        is_secret = any(upper.endswith(s) for s in secret_suffixes)
        if not is_secret:
            continue

        result.checked += 1
        raw_date = pin_dates.get(key)
        if raw_date is None:
            result.issues.append(
                RotationIssue(
                    key=key,
                    pinned_date=None,
                    age_days=None,
                    reason="No rotation date pinned for secret key.",
                )
            )
            continue

        pinned = _parse_date(raw_date)
        if pinned is None:
            result.issues.append(
                RotationIssue(
                    key=key,
                    pinned_date=None,
                    age_days=None,
                    reason=f"Invalid date format '{raw_date}'; expected YYYY-MM-DD.",
                )
            )
            continue

        age = (today - pinned).days
        if age > max_age_days:
            result.issues.append(
                RotationIssue(
                    key=key,
                    pinned_date=pinned,
                    age_days=age,
                    reason=f"Key is {age} day(s) old; exceeds {max_age_days}-day limit.",
                )
            )

    return result
