"""freezer.py – snapshot an env dict into an immutable 'frozen' record and detect thaw (drift)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class FreezeResult:
    env: Dict[str, str]
    checksum: str

    @property
    def key_count(self) -> int:
        return len(self.env)

    def summary(self) -> str:
        return f"Frozen {self.key_count} key(s) [checksum={self.checksum[:8]}]"

    def save(self, path: Path) -> None:
        payload = {"env": self.env, "checksum": self.checksum}
        path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> "FreezeResult":
        payload = json.loads(path.read_text())
        return cls(env=payload["env"], checksum=payload["checksum"])


@dataclass
class ThawResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        if not self.has_drift:
            return "No drift detected – env matches frozen state."
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return "Drift detected: " + ", ".join(parts)


def _checksum(env: Dict[str, str]) -> str:
    serialized = json.dumps(dict(sorted(env.items())), sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()


def freeze_env(env: Dict[str, str]) -> FreezeResult:
    """Freeze *env* into an immutable record with a deterministic checksum."""
    return FreezeResult(env=dict(env), checksum=_checksum(env))


def thaw_env(frozen: FreezeResult, current: Dict[str, str]) -> ThawResult:
    """Compare *current* env against a previously frozen state."""
    frozen_keys = set(frozen.env)
    current_keys = set(current)
    result = ThawResult(
        added=sorted(current_keys - frozen_keys),
        removed=sorted(frozen_keys - current_keys),
        changed=sorted(
            k for k in frozen_keys & current_keys if frozen.env[k] != current[k]
        ),
    )
    return result
