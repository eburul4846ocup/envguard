"""Inject environment variables into a process environment or shell export block."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InjectResult:
    """Result of an injection operation."""

    injected: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)
    overridden: Dict[str, str] = field(default_factory=dict)

    @property
    def inject_count(self) -> int:
        return len(self.injected)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    @property
    def override_count(self) -> int:
        return len(self.overridden)

    @property
    def is_changed(self) -> bool:
        return bool(self.injected or self.overridden)

    def summary(self) -> str:
        parts = [f"injected={self.inject_count}"]
        if self.skip_count:
            parts.append(f"skipped={self.skip_count}")
        if self.override_count:
            parts.append(f"overridden={self.override_count}")
        return ", ".join(parts)

    def merged_env(self, base: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Return the final merged environment dict."""
        result: Dict[str, str] = dict(base or {})
        result.update(self.injected)
        result.update(self.overridden)
        return result


def inject_env(
    source: Dict[str, str],
    target: Optional[Dict[str, str]] = None,
    *,
    override: bool = False,
    keys: Optional[List[str]] = None,
) -> InjectResult:
    """Inject *source* variables into *target*.

    Args:
        source:   Variables to inject.
        target:   Existing environment (e.g. ``os.environ``).  Defaults to ``{}``.
        override: When *True*, existing keys in *target* are overwritten and
                  recorded in ``InjectResult.overridden``.
        keys:     Explicit allow-list of keys to inject.  If *None*, all keys
                  from *source* are considered.
    """
    target = dict(target or {})
    result = InjectResult()

    candidates = {k: v for k, v in source.items() if keys is None or k in keys}

    for key, value in candidates.items():
        if key in target:
            if override:
                result.overridden[key] = value
            else:
                result.skipped[key] = value
        else:
            result.injected[key] = value

    return result
