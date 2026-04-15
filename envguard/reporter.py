"""Formats and outputs comparison results for human or machine consumption."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from envguard.comparator import ComparisonResult


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


def _color(text: str, code: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def report_text(
    result: ComparisonResult,
    source_name: str = ".env",
    target_name: str = ".env.target",
    out: TextIO = sys.stdout,
    use_color: bool = True,
) -> None:
    """Write a human-readable diff report to *out*."""
    red = lambda t: _color(t, "31", use_color)
    yellow = lambda t: _color(t, "33", use_color)
    green = lambda t: _color(t, "32", use_color)
    bold = lambda t: _color(t, "1", use_color)

    if not result.has_differences():
        out.write(green("✔ No differences found.") + "\n")
        return

    out.write(bold(f"Comparing {source_name} → {target_name}") + "\n")
    out.write("\n")

    if result.missing_keys:
        out.write(bold("Missing keys in target:") + "\n")
        for key in sorted(result.missing_keys):
            out.write(f"  {red('-')} {key}\n")
        out.write("\n")

    if result.extra_keys:
        out.write(bold("Extra keys in target (not in source):") + "\n")
        for key in sorted(result.extra_keys):
            out.write(f"  {yellow('+')} {key}\n")
        out.write("\n")

    if result.mismatched_values:
        out.write(bold("Value mismatches:") + "\n")
        for key, (src_val, tgt_val) in sorted(result.mismatched_values.items()):
            out.write(f"  {key}:\n")
            out.write(f"    {red('source')}: {src_val!r}\n")
            out.write(f"    {green('target')}: {tgt_val!r}\n")
        out.write("\n")

    out.write(result.summary() + "\n")


def report_json(
    result: ComparisonResult,
    source_name: str = ".env",
    target_name: str = ".env.target",
    out: TextIO = sys.stdout,
) -> None:
    """Write a machine-readable JSON report to *out*."""
    import json

    payload = {
        "source": source_name,
        "target": target_name,
        "has_differences": result.has_differences(),
        "missing_keys": sorted(result.missing_keys),
        "extra_keys": sorted(result.extra_keys),
        "mismatched_values": {
            k: {"source": sv, "target": tv}
            for k, (sv, tv) in sorted(result.mismatched_values.items())
        },
    }
    json.dump(payload, out, indent=2)
    out.write("\n")
