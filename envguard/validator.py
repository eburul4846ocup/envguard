"""Validates .env files against a schema/template for required keys and value formats."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


VALUE_PATTERNS: Dict[str, str] = {
    "url": r"^https?://.+",
    "port": r"^\d{1,5}$",
    "bool": r"^(true|false|True|False|TRUE|FALSE|1|0)$",
    "email": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    "nonempty": r".+",
}


def validate_env(
    env: Dict[str, str],
    required_keys: Optional[List[str]] = None,
    key_patterns: Optional[Dict[str, str]] = None,
    allow_empty_values: bool = False,
) -> ValidationResult:
    """Validate an env dict against required keys and optional value-format rules.

    Args:
        env: Parsed environment variables.
        required_keys: Keys that must be present.
        key_patterns: Mapping of key -> pattern name (from VALUE_PATTERNS) or raw regex.
        allow_empty_values: If False, warn on keys with empty string values.
    """
    result = ValidationResult()

    for key, value in env.items():
        if not allow_empty_values and value == "":
            result.issues.append(
                ValidationIssue(key, "value is empty", severity="warning")
            )

    if required_keys:
        for key in required_keys:
            if key not in env:
                result.issues.append(
                    ValidationIssue(key, "required key is missing", severity="error")
                )

    if key_patterns:
        for key, pattern_or_name in key_patterns.items():
            if key not in env:
                continue
            pattern = VALUE_PATTERNS.get(pattern_or_name, pattern_or_name)
            if not re.match(pattern, env[key]):
                result.issues.append(
                    ValidationIssue(
                        key,
                        f"value '{env[key]}' does not match pattern '{pattern_or_name}'",
                        severity="error",
                    )
                )

    return result
