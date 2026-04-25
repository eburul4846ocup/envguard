"""Classify .env keys by type: secret, url, flag, numeric, or plain."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

_SECRET_FRAGMENTS = ("secret", "password", "passwd", "token", "key", "api_key", "private", "auth")
_URL_FRAGMENTS = ("url", "uri", "endpoint", "host", "dsn", "database_url")
_FLAG_FRAGMENTS = ("enable", "disable", "flag", "debug", "verbose", "active", "enabled")


def _classify_key(key: str, value: str) -> str:
    lower = key.lower()
    if any(f in lower for f in _SECRET_FRAGMENTS):
        return "secret"
    if any(f in lower for f in _URL_FRAGMENTS):
        return "url"
    if any(f in lower for f in _FLAG_FRAGMENTS):
        return "flag"
    if value.strip().lstrip("-").replace(".", "", 1).isdigit():
        return "numeric"
    return "plain"


@dataclass
class ClassifyResult:
    groups: Dict[str, List[str]] = field(default_factory=dict)
    key_types: Dict[str, str] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return len(self.key_types)

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def summary(self) -> str:
        parts = [f"{k}: {len(v)}" for k, v in sorted(self.groups.items())]
        return f"total={self.total_keys} " + " ".join(parts)


def classify_env(env: Dict[str, str]) -> ClassifyResult:
    """Classify each key in *env* and return a ClassifyResult."""
    groups: Dict[str, List[str]] = {}
    key_types: Dict[str, str] = {}

    for key, value in env.items():
        category = _classify_key(key, value)
        key_types[key] = category
        groups.setdefault(category, []).append(key)

    # Sort keys within each group for deterministic output
    for cat in groups:
        groups[cat].sort()

    return ClassifyResult(groups=groups, key_types=key_types)
