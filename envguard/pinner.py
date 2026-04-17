"""Pin current env variable values to a lockfile for drift detection."""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class PinResult:
    pinned: Dict[str, str]
    source: str
    checksum: str

    def key_count(self) -> int:
        return len(self.pinned)

    def summary(self) -> str:
        return f"Pinned {self.key_count()} keys from '{self.source}' (checksum: {self.checksum[:8]})"


@dataclass
class DriftResult:
    drifted: Dict[str, tuple]  # key -> (pinned_value, current_value)
    added: List[str]
    removed: List[str]

    def has_drift(self) -> bool:
        return bool(self.drifted or self.added or self.removed)

    def summary(self) -> str:
        parts = []
        if self.drifted:
            parts.append(f"{len(self.drifted)} changed")
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        return ", ".join(parts) if parts else "No drift detected"


def _checksum(data: Dict[str, str]) -> str:
    blob = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def pin_env(env: Dict[str, str], source: str) -> PinResult:
    pinned = dict(sorted(env.items()))
    return PinResult(pinned=pinned, source=source, checksum=_checksum(pinned))


def save_pin(result: PinResult, path: Path) -> None:
    payload = {"source": result.source, "checksum": result.checksum, "pinned": result.pinned}
    path.write_text(json.dumps(payload, indent=2))


def load_pin(path: Path) -> PinResult:
    payload = json.loads(path.read_text())
    return PinResult(pinned=payload["pinned"], source=payload["source"], checksum=payload["checksum"])


def detect_drift(pin: PinResult, current: Dict[str, str]) -> DriftResult:
    drifted = {}
    for k, v in pin.pinned.items():
        if k in current and current[k] != v:
            drifted[k] = (v, current[k])
    added = [k for k in current if k not in pin.pinned]
    removed = [k for k in pin.pinned if k not in current]
    return DriftResult(drifted=drifted, added=added, removed=removed)
