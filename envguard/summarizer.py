"""Summarize an .env file into a human-readable report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

SECRET_HINTS = ("secret", "password", "passwd", "token", "key", "api", "auth", "private")


@dataclass
class SummaryResult:
    total_keys: int
    empty_keys: List[str] = field(default_factory=list)
    secret_keys: List[str] = field(default_factory=list)
    plain_keys: List[str] = field(default_factory=list)

    def empty_count(self) -> int:
        return len(self.empty_keys)

    def secret_count(self) -> int:
        return len(self.secret_keys)

    def plain_count(self) -> int:
        return len(self.plain_keys)

    def summary(self) -> str:
        return (
            f"Total keys  : {self.total_keys}\n"
            f"Secret keys : {self.secret_count()}\n"
            f"Plain keys  : {self.plain_count()}\n"
            f"Empty keys  : {self.empty_count()}"
        )


def _is_secret(key: str) -> bool:
    lower = key.lower()
    return any(hint in lower for hint in SECRET_HINTS)


def summarize_env(env: Dict[str, str]) -> SummaryResult:
    """Classify each key and return a SummaryResult."""
    empty: List[str] = []
    secret: List[str] = []
    plain: List[str] = []

    for key, value in env.items():
        if not value:
            empty.append(key)
        if _is_secret(key):
            secret.append(key)
        else:
            plain.append(key)

    return SummaryResult(
        total_keys=len(env),
        empty_keys=sorted(empty),
        secret_keys=sorted(secret),
        plain_keys=sorted(plain),
    )
