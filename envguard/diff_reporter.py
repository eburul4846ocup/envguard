"""Render an :class:`EnvDiff` as text or JSON."""
from __future__ import annotations

import json
from typing import List

from envguard.differ import EnvDiff, DiffEntry
from envguard.reporter import OutputFormat, _color

_STATUS_COLOR = {
    "added":     "green",
    "removed":   "red",
    "changed":   "yellow",
    "unchanged": None,
}


def _fmt_entry(entry: DiffEntry, use_color: bool) -> str:
    color = _STATUS_COLOR.get(entry.status)
    line = str(entry)
    if use_color and color:
        line = _color(line, color)
    return line


def report_diff_text(diff: EnvDiff, use_color: bool = True) -> str:
    lines: List[str] = [
        f"--- {diff.source_path}",
        f"+++ {diff.target_path}",
        "",
    ]
    if not diff.has_changes:
        lines.append("No differences found.")
        return "\n".join(lines)

    for entry in diff.entries:
        lines.append(_fmt_entry(entry, use_color))

    summary_parts = []
    if diff.added:
        summary_parts.append(f"{len(diff.added)} added")
    if diff.removed:
        summary_parts.append(f"{len(diff.removed)} removed")
    if diff.changed:
        summary_parts.append(f"{len(diff.changed)} changed")

    lines.append("")
    lines.append("Summary: " + ", ".join(summary_parts))
    return "\n".join(lines)


def report_diff_json(diff: EnvDiff) -> str:
    payload = {
        "source": diff.source_path,
        "target": diff.target_path,
        "has_changes": diff.has_changes,
        "entries": [
            {
                "key": e.key,
                "status": e.status,
                "source_value": e.source_value,
                "target_value": e.target_value,
            }
            for e in diff.entries
        ],
    }
    return json.dumps(payload, indent=2)
