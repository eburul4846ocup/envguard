"""Aliaser: rename env keys using an alias map while preserving originals optionally."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AliasResult:
    """Result of applying an alias map to an env dict."""

    env: Dict[str, str]
    applied: List[str] = field(default_factory=list)   # alias keys written
    skipped: List[str] = field(default_factory=list)   # alias source not found
    removed: List[str] = field(default_factory=list)   # original keys dropped

    @property
    def change_count(self) -> int:  # noqa: D401
        return len(self.applied)

    @property
    def is_changed(self) -> bool:
        return bool(self.applied or self.removed)

    def summary(self) -> str:
        parts = [f"{self.change_count} alias(es) applied"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped (source missing)")
        if self.removed:
            parts.append(f"{len(self.removed)} original(s) removed")
        return ", ".join(parts)

    def to_string(self) -> str:
        """Serialise env back to .env format."""
        return "".join(f"{k}={v}\n" for k, v in sorted(self.env.items()))


def alias_env(
    env: Dict[str, str],
    aliases: Dict[str, str],
    *,
    keep_original: bool = False,
) -> AliasResult:
    """Apply *aliases* mapping ``{new_key: old_key}`` to *env*.

    Parameters
    ----------
    env:
        Parsed environment dict.
    aliases:
        Mapping of ``new_name -> existing_name``.
    keep_original:
        When *True* the source key is kept alongside the new alias key.
        When *False* (default) the source key is removed after aliasing.
    """
    result: Dict[str, str] = dict(env)
    applied: List[str] = []
    skipped: List[str] = []
    removed: List[str] = []

    for new_key, old_key in aliases.items():
        if old_key not in result:
            skipped.append(new_key)
            continue
        result[new_key] = result[old_key]
        applied.append(new_key)
        if not keep_original and old_key != new_key:
            del result[old_key]
            removed.append(old_key)

    return AliasResult(env=result, applied=applied, skipped=skipped, removed=removed)
