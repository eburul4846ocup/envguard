"""Cross-environment key presence and value diff across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envguard.parser import parse_env_file


@dataclass
class EnvKeyReport:
    """Per-key presence/value report across all environments."""

    key: str
    values: Dict[str, Optional[str]] = field(default_factory=dict)  # env_name -> value

    @property
    def is_consistent(self) -> bool:
        """True when every environment that has the key shares the same value."""
        present = [v for v in self.values.values() if v is not None]
        return len(set(present)) <= 1

    @property
    def missing_in(self) -> List[str]:
        return [name for name, v in self.values.items() if v is None]


@dataclass
class MultiEnvDiff:
    env_names: List[str]
    reports: List[EnvKeyReport] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(not r.is_consistent or r.missing_in for r in self.reports)

    @property
    def inconsistent_keys(self) -> List[EnvKeyReport]:
        return [r for r in self.reports if not r.is_consistent]

    @property
    def keys_with_gaps(self) -> List[EnvKeyReport]:
        return [r for r in self.reports if r.missing_in]

    def summary(self) -> str:
        total = len(self.reports)
        gaps = len(self.keys_with_gaps)
        inconsistent = len(self.inconsistent_keys)
        return (
            f"{total} keys scanned across {len(self.env_names)} environments; "
            f"{gaps} with missing presence, {inconsistent} with value mismatches."
        )


def diff_many(env_paths: Dict[str, Path]) -> MultiEnvDiff:
    """Diff key presence and values across multiple named .env files."""
    parsed: Dict[str, Dict[str, str]] = {
        name: parse_env_file(path) for name, path in env_paths.items()
    }
    env_names = list(parsed.keys())
    all_keys: set = set()
    for env in parsed.values():
        all_keys.update(env.keys())

    reports: List[EnvKeyReport] = []
    for key in sorted(all_keys):
        values = {name: parsed[name].get(key) for name in env_names}
        reports.append(EnvKeyReport(key=key, values=values))

    return MultiEnvDiff(env_names=env_names, reports=reports)
