"""Audit .env files for secret-like values that should not be committed."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class AuditSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


# Patterns that suggest a value may be a secret / credential
_SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth)"),
    re.compile(r"(?i)(access[_-]?key|client[_-]?secret|signing[_-]?key)"),
]

# Patterns that indicate a value looks like a real secret (not a placeholder)
_PLACEHOLDER_PATTERN = re.compile(
    r"^(changeme|placeholder|your[_-]|<.*>|\$\{.*\}|TODO|FIXME|xxx+)$",
    re.IGNORECASE,
)


@dataclass
class AuditIssue:
    key: str
    message: str
    severity: AuditSeverity

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.key}: {self.message}"


@dataclass
class AuditResult:
    issues: List[AuditIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == AuditSeverity.ERROR]

    @property
    def warnings(self) -> List[AuditIssue]:
        return [i for i in self.issues if i.severity == AuditSeverity.WARNING]


def audit_env(
    env: Dict[str, str],
    *,
    flag_placeholders: bool = True,
) -> AuditResult:
    """Audit *env* dict for potential secret exposure issues.

    Parameters
    ----------
    env:
        Parsed key/value pairs from a .env file.
    flag_placeholders:
        When True, warn if a secret-like key has an obvious placeholder value.
    """
    result = AuditResult()

    for key, value in env.items():
        is_secret_key = any(p.search(key) for p in _SECRET_PATTERNS)
        if not is_secret_key:
            continue

        if not value:
            result.issues.append(
                AuditIssue(
                    key=key,
                    message="secret-like key has an empty value",
                    severity=AuditSeverity.WARNING,
                )
            )
        elif flag_placeholders and _PLACEHOLDER_PATTERN.match(value):
            result.issues.append(
                AuditIssue(
                    key=key,
                    message=f"secret-like key appears to use a placeholder value: {value!r}",
                    severity=AuditSeverity.WARNING,
                )
            )
        else:
            result.issues.append(
                AuditIssue(
                    key=key,
                    message="secret-like key contains a non-placeholder value — ensure this file is not committed",
                    severity=AuditSeverity.ERROR,
                )
            )

    return result
