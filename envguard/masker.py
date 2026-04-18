"""Mask env values for safe display in logs or CI output."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set

_SENSITIVE_FRAGMENTS = ("secret", "password", "passwd", "token", "key", "api", "auth", "credential", "private")


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(frag in lower for frag in _SENSITIVE_FRAGMENTS)


@dataclass
class MaskResult:
    masked: Dict[str, str]
    masked_keys: Set[str] = field(default_factory=set)

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)

    @property
    def is_changed(self) -> bool:
        return self.mask_count > 0

    def summary(self) -> str:
        if not self.is_changed:
            return "No sensitive keys found; nothing masked."
        keys = ", ".join(sorted(self.masked_keys))
        return f"{self.mask_count} key(s) masked: {keys}"


def mask_env(
    env: Dict[str, str],
    mask_char: str = "*",
    visible_chars: int = 0,
    custom_keys: Set[str] | None = None,
) -> MaskResult:
    """Return a copy of *env* with sensitive values replaced.

    Args:
        env: Parsed environment mapping.
        mask_char: Character used to build the mask string.
        visible_chars: How many trailing characters to leave visible (0 = full mask).
        custom_keys: Additional key names to treat as sensitive.
    """
    extra: Set[str] = {k.lower() for k in (custom_keys or set())}
    result: Dict[str, str] = {}
    masked_keys: Set[str] = set()

    for key, value in env.items():
        if _is_sensitive(key) or key.lower() in extra:
            if visible_chars and len(value) > visible_chars:
                masked_value = mask_char * (len(value) - visible_chars) + value[-visible_chars:]
            else:
                masked_value = mask_char * max(len(value), 6)
            result[key] = masked_value
            masked_keys.add(key)
        else:
            result[key] = value

    return MaskResult(masked=result, masked_keys=masked_keys)
