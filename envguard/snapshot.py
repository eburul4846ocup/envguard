"""Snapshot: capture and compare .env state over time."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Snapshot:
    """A point-in-time capture of an .env file's keys and values."""

    source: str
    captured_at: float
    env: Dict[str, str]
    label: Optional[str] = None

    # ------------------------------------------------------------------ #
    def keys_added_since(self, previous: "Snapshot") -> List[str]:
        """Keys present in *self* but absent in *previous*."""
        return sorted(set(self.env) - set(previous.env))

    def keys_removed_since(self, previous: "Snapshot") -> List[str]:
        """Keys present in *previous* but absent in *self*."""
        return sorted(set(previous.env) - set(self.env))

    def keys_changed_since(self, previous: "Snapshot") -> List[str]:
        """Keys whose values differ between *previous* and *self*."""
        return sorted(
            k for k in set(self.env) & set(previous.env)
            if self.env[k] != previous.env[k]
        )

    def has_changes_since(self, previous: "Snapshot") -> bool:
        return bool(
            self.keys_added_since(previous)
            or self.keys_removed_since(previous)
            or self.keys_changed_since(previous)
        )

    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "label": self.label,
            "env": self.env,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            source=data["source"],
            captured_at=data["captured_at"],
            label=data.get("label"),
            env=data["env"],
        )


def capture(env: Dict[str, str], source: str, label: Optional[str] = None) -> Snapshot:
    """Create a new :class:`Snapshot` from an env mapping."""
    return Snapshot(source=source, captured_at=time.time(), env=dict(env), label=label)


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Persist *snapshot* to *path* as JSON."""
    path.write_text(json.dumps(snapshot.to_dict(), indent=2))


def load_snapshot(path: Path) -> Snapshot:
    """Load a :class:`Snapshot` previously saved by :func:`save_snapshot`."""
    return Snapshot.from_dict(json.loads(path.read_text()))
