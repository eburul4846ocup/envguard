"""Flatten nested key structures by replacing a separator with a flat delimiter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FlattenResult:
    """Result of a flatten operation."""
    original: Dict[str, str]
    flattened: Dict[str, str]
    renamed: List[str] = field(default_factory=list)

    @property
    def change_count(self) -> int:
        return len(self.renamed)

    @property
    def is_changed(self) -> bool:
        return self.change_count > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "No keys required flattening."
        return (
            f"{self.change_count} key(s) flattened; "
            f"{len(self.flattened)} total key(s) in output."
        )

    def to_string(self) -> str:
        lines = []
        for key, value in self.flattened.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)


def flatten_env(
    env: Dict[str, str],
    *,
    from_sep: str = ".",
    to_sep: str = "_",
    uppercase: bool = True,
) -> FlattenResult:
    """Return a new env dict with *from_sep* replaced by *to_sep* in every key.

    Args:
        env:        Source key/value mapping.
        from_sep:   Separator to replace (default ``"."``).  Keys that do not
                    contain *from_sep* are copied unchanged.
        to_sep:     Replacement separator (default ``"_"``).
        uppercase:  When *True* (default) the resulting key is uppercased.
    """
    flattened: Dict[str, str] = {}
    renamed: List[str] = []

    for key, value in env.items():
        if from_sep in key:
            new_key = key.replace(from_sep, to_sep)
            if uppercase:
                new_key = new_key.upper()
            flattened[new_key] = value
            renamed.append(key)
        else:
            out_key = key.upper() if uppercase else key
            flattened[out_key] = value

    return FlattenResult(original=dict(env), flattened=flattened, renamed=renamed)
