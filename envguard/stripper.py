"""Strip comments and blank lines from .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StripResult:
    original_lines: int
    stripped_lines: int
    removed_comments: int
    removed_blanks: int
    lines: list[str] = field(default_factory=list)

    @property
    def is_changed(self) -> bool:
        return self.original_lines != self.stripped_lines

    def summary(self) -> str:
        if not self.is_changed:
            return "Nothing to strip."
        return (
            f"Removed {self.removed_comments} comment(s) and "
            f"{self.removed_blanks} blank line(s); "
            f"{self.stripped_lines} line(s) remain."
        )

    def to_string(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines else "")


def strip_env(path: Path, *, keep_blanks: bool = False, keep_comments: bool = False) -> StripResult:
    raw = path.read_text(encoding="utf-8").splitlines()
    original = len(raw)
    out: list[str] = []
    removed_comments = 0
    removed_blanks = 0

    for line in raw:
        stripped = line.strip()
        if stripped.startswith("#"):
            if keep_comments:
                out.append(line)
            else:
                removed_comments += 1
        elif stripped == "":
            if keep_blanks:
                out.append(line)
            else:
                removed_blanks += 1
        else:
            out.append(line)

    return StripResult(
        original_lines=original,
        stripped_lines=len(out),
        removed_comments=removed_comments,
        removed_blanks=removed_blanks,
        lines=out,
    )
