"""Prefixer: add or remove a prefix from all keys in an env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PrefixResult:
    """Result of a prefix operation."""

    env: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:  # noqa: D401
        """Number of keys that were renamed."""
        return len(self.changed_keys)

    @property
    def is_changed(self) -> bool:
        return self.change_count > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "No keys were modified."
        parts = [f"{self.change_count} key(s) modified."]
        if self.skipped_keys:
            parts.append(f"{len(self.skipped_keys)} key(s) skipped (already prefixed).")
        return " ".join(parts)

    def to_string(self) -> str:
        """Render the result as a .env-formatted string."""
        lines = [f"{k}={v}" for k, v in sorted(self.env.items())]
        return "\n".join(lines) + ("\n" if lines else "")


def add_prefix(
    env: Dict[str, str],
    prefix: str,
    *,
    skip_existing: bool = True,
) -> PrefixResult:
    """Return a new env dict with *prefix* prepended to every key.

    Args:
        env: Source key/value mapping.
        prefix: String to prepend (e.g. ``"APP_"``).
        skip_existing: When *True*, keys that already start with *prefix*
            are left unchanged and recorded in ``skipped_keys``.
    """
    out: Dict[str, str] = {}
    changed: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        if key.startswith(prefix):
            if skip_existing:
                out[key] = value
                skipped.append(key)
            else:
                new_key = prefix + key
                out[new_key] = value
                changed.append(key)
        else:
            new_key = prefix + key
            out[new_key] = value
            changed.append(key)

    return PrefixResult(env=out, changed_keys=changed, skipped_keys=skipped)


def remove_prefix(
    env: Dict[str, str],
    prefix: str,
) -> PrefixResult:
    """Return a new env dict with *prefix* stripped from every matching key.

    Keys that do not start with *prefix* are kept as-is and recorded in
    ``skipped_keys``.
    """
    out: Dict[str, str] = {}
    changed: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            out[new_key] = value
            changed.append(key)
        else:
            out[key] = value
            skipped.append(key)

    return PrefixResult(env=out, changed_keys=changed, skipped_keys=skipped)
