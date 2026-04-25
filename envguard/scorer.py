"""Score an .env file on a 0-100 quality scale."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Penalty points per issue type
_PENALTIES: Dict[str, int] = {
    "empty_value": 5,
    "secret_plain": 15,
    "no_uppercase": 3,
    "duplicate_key": 10,
    "placeholder_value": 8,
    "very_long_value": 2,
}

_SECRET_HINTS = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "API_KEY", "PRIVATE")
_PLACEHOLDER_HINTS = ("<", ">", "CHANGE_ME", "TODO", "PLACEHOLDER", "FIXME")


@dataclass
class ScoreResult:
    score: int
    penalties: List[str] = field(default_factory=list)
    total_keys: int = 0

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 60:
            return "C"
        if self.score >= 40:
            return "D"
        return "F"

    def summary(self) -> str:
        return (
            f"Score: {self.score}/100 (Grade: {self.grade}) "
            f"| Keys: {self.total_keys} | Penalties: {len(self.penalties)}"
        )


def score_env(
    env: Dict[str, str],
    *,
    require_uppercase: bool = True,
) -> ScoreResult:
    """Analyse *env* and return a ScoreResult."""
    if not env:
        return ScoreResult(score=100, total_keys=0)

    penalties: List[str] = []
    seen: Dict[str, int] = {}

    for key, value in env.items():
        seen[key] = seen.get(key, 0) + 1

        if value == "":
            penalties.append(f"empty_value:{key}")

        upper_key = key.upper()
        is_secret = any(hint in upper_key for hint in _SECRET_HINTS)
        if is_secret and value and not value.startswith("${"):
            # plain-text secret stored verbatim
            penalties.append(f"secret_plain:{key}")

        if require_uppercase and key != key.upper():
            penalties.append(f"no_uppercase:{key}")

        if any(hint in value for hint in _PLACEHOLDER_HINTS):
            penalties.append(f"placeholder_value:{key}")

        if len(value) > 512:
            penalties.append(f"very_long_value:{key}")

    for key, count in seen.items():
        if count > 1:
            penalties.append(f"duplicate_key:{key}")

    total_deduction = sum(
        _PENALTIES.get(p.split(":")[0], 0) for p in penalties
    )
    score = max(0, 100 - total_deduction)
    return ScoreResult(score=score, penalties=penalties, total_keys=len(env))
