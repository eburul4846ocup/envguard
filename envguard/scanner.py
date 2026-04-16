"""Scan .env files for hardcoded secrets using pattern matching."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List

_PATTERNS: Dict[str, re.Pattern] = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key": re.compile(r"[A-Za-z0-9/+=]{40}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "private_key_header": re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    "hex_secret": re.compile(r"[0-9a-fA-F]{32,64}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
}


@dataclass
class ScanHit:
    key: str
    value: str
    pattern_name: str

    def __str__(self) -> str:
        masked = self.value[:4] + "****" if len(self.value) > 4 else "****"
        return f"{self.key}: matched '{self.pattern_name}' (value: {masked})"


@dataclass
class ScanResult:
    hits: List[ScanHit] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.hits) == 0

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    def summary(self) -> str:
        if self.is_clean:
            return "No hardcoded secrets detected."
        lines = [f"{self.hit_count} potential secret(s) detected:"]
        for h in self.hits:
            lines.append(f"  ! {h}")
        return "\n".join(lines)


def scan_env(env: Dict[str, str]) -> ScanResult:
    """Scan env dict values against known secret patterns."""
    hits: List[ScanHit] = []
    for key, value in env.items():
        if not value:
            continue
        for pattern_name, pattern in _PATTERNS.items():
            if pattern.search(value):
                hits.append(ScanHit(key=key, value=value, pattern_name=pattern_name))
                break  # one hit per key is enough
    return ScanResult(hits=hits)
