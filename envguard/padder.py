"""Pad .env values to a consistent alignment width.

All keys are left-padded so that the '=' sign lines up at the same
column, making the file easier to read at a glance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PadResult:
    """Result of a padding operation."""

    original: Dict[str, str]
    padded: Dict[str, str]  # same values, keys unchanged
    width: int  # column at which '=' appears

    @property
    def change_count(self) -> int:  # noqa: D401
        """Number of lines whose formatting actually changed."""
        return sum(
            1
            for k, v in self.original.items()
            if f"{k}={v}" != f"{k:<{self.width}}={v}"
        )

    @property
    def is_changed(self) -> bool:
        return self.change_count > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "pad: no changes (already aligned or empty)"
        return (
            f"pad: aligned {self.change_count} key(s) "
            f"to width {self.width}"
        )

    def to_string(self) -> str:
        """Render the padded env as a .env-formatted string."""
        lines = [
            f"{k:<{self.width}}={v}" for k, v in self.padded.items()
        ]
        return "\n".join(lines) + ("\n" if lines else "")


def pad_env(
    env: Dict[str, str],
    *,
    min_width: int = 0,
) -> PadResult:
    """Return a *PadResult* whose keys are aligned to the longest key.

    Parameters
    ----------
    env:
        Parsed key/value mapping.
    min_width:
        Minimum column width for the key field (default 0 means
        derive purely from the longest key present).
    """
    if not env:
        return PadResult(original={}, padded={}, width=max(min_width, 0))

    width = max(max(len(k) for k in env), min_width)
    padded = {k: v for k, v in env.items()}  # values unchanged
    return PadResult(original=dict(env), padded=padded, width=width)
