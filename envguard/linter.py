"""Lint .env files for style and convention issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envguard.parser import parse_env_file

_UPPER_SNAKE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_NO_SPACES = re.compile(r'\s')


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"line {self.line}: [{self.code}] {self.key!r} — {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.code.startswith('E')]

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.code.startswith('W')]


def lint_env_file(
    path: Path,
    *,
    require_uppercase: bool = True,
    warn_no_value: bool = True,
    warn_duplicate: bool = True,
) -> LintResult:
    """Lint *path* and return a :class:`LintResult`."""
    result = LintResult()
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    seen: dict[str, int] = {}

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' not in stripped:
            result.issues.append(
                LintIssue(lineno, stripped, 'E001', 'Line is not a valid KEY=VALUE assignment')
            )
            continue

        key, _, value = stripped.partition('=')
        key = key.strip()

        if _NO_SPACES.search(key):
            result.issues.append(
                LintIssue(lineno, key, 'E002', 'Key contains whitespace')
            )

        if require_uppercase and not _UPPER_SNAKE.match(key):
            result.issues.append(
                LintIssue(lineno, key, 'W001', 'Key should be UPPER_SNAKE_CASE')
            )

        if warn_no_value and value.strip() == '':
            result.issues.append(
                LintIssue(lineno, key, 'W002', 'Key has no value assigned')
            )

        if warn_duplicate and key in seen:
            result.issues.append(
                LintIssue(
                    lineno, key, 'W003',
                    f'Duplicate key (first seen on line {seen[key]})'
                )
            )
        else:
            seen[key] = lineno

    return result
