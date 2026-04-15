"""Redact sensitive values in .env data before display or export."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

# Keywords that indicate a value should be treated as sensitive
_SECRET_HINTS = (
    "SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE",
    "CREDENTIAL", "AUTH", "API_KEY", "APIKEY", "CERT", "PASS",
)

DEFAULT_MASK = "***"


def _is_sensitive(key: str) -> bool:
    upper = key.upper()
    return any(hint in upper for hint in _SECRET_HINTS)


@dataclass
class RedactionResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def redaction_count(self) -> int:
        return len(self.redacted_keys)

    def summary(self) -> str:
        if not self.redacted_keys:
            return "No sensitive keys redacted."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"Redacted {self.redaction_count} sensitive key(s): {keys}"


def redact_env(
    env: Dict[str, str],
    mask: str = DEFAULT_MASK,
    extra_keys: Set[str] | None = None,
) -> RedactionResult:
    """Return a RedactionResult with sensitive values replaced by *mask*.

    Args:
        env: Mapping of key -> value parsed from a .env file.
        mask: Replacement string for sensitive values.
        extra_keys: Additional key names (case-insensitive) to always redact.
    """
    extra_upper: Set[str] = {k.upper() for k in (extra_keys or set())}
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        if _is_sensitive(key) or key.upper() in extra_upper:
            redacted[key] = mask
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactionResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=sorted(redacted_keys),
    )
