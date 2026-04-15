"""Profile an .env file: summarise key statistics and categorise variables."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_SECRET_PATTERN = re.compile(
    r"(secret|password|passwd|token|key|api_key|private|credential|auth)",
    re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_BOOL_VALUES = {"true", "false", "1", "0", "yes", "no"}


@dataclass
class ProfileResult:
    total_keys: int = 0
    empty_values: List[str] = field(default_factory=list)
    secret_keys: List[str] = field(default_factory=list)
    url_values: List[str] = field(default_factory=list)
    boolean_values: List[str] = field(default_factory=list)
    numeric_values: List[str] = field(default_factory=list)
    plain_values: List[str] = field(default_factory=list)

    def summary(self) -> Dict[str, int]:
        return {
            "total": self.total_keys,
            "empty": len(self.empty_values),
            "secrets": len(self.secret_keys),
            "urls": len(self.url_values),
            "booleans": len(self.boolean_values),
            "numeric": len(self.numeric_values),
            "plain": len(self.plain_values),
        }


def profile_env(env: Dict[str, str]) -> ProfileResult:
    """Analyse *env* and return a :class:`ProfileResult`."""
    result = ProfileResult(total_keys=len(env))

    for key, value in env.items():
        stripped = value.strip()

        if stripped == "":
            result.empty_values.append(key)
            continue

        if _SECRET_PATTERN.search(key):
            result.secret_keys.append(key)

        if _URL_PATTERN.match(stripped):
            result.url_values.append(key)
        elif stripped.lower() in _BOOL_VALUES:
            result.boolean_values.append(key)
        elif re.match(r"^-?\d+(\.\d+)?$", stripped):
            result.numeric_values.append(key)
        else:
            result.plain_values.append(key)

    return result
