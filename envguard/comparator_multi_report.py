"""Report formatting for multi-environment comparison results."""

from __future__ import annotations

import json
from typing import Dict, List

from .multi_comparator import compare_many
from .comparator import ComparisonResult

# ANSI colour helpers
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"


def _color(text: str, code: str, *, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{code}{text}{_RESET}"


def report_multi_comparison_text(
    results: Dict[str, ComparisonResult],
    *,
    use_color: bool = True,
) -> str:
    """Render a human-readable multi-environment comparison report.

    Args:
        results: Mapping of target-label -> ComparisonResult produced by
                 :func:`~envguard.multi_comparator.compare_many`.
        use_color: Whether to emit ANSI colour codes.

    Returns:
        A formatted string suitable for printing to a terminal.
    """
    if not results:
        return _color("No comparison results.", _YELLOW, use_color=use_color)

    lines: List[str] = []

    for label, result in results.items():
        header = f"=== {label} ==="
        lines.append(_color(header, _YELLOW, use_color=use_color))

        if not result.has_differences():
            lines.append(_color("  ✓ No differences found.", _GREEN, use_color=use_color))
            lines.append("")
            continue

        if result.missing_keys:
            lines.append(_color("  Missing keys:", _RED, use_color=use_color))
            for key in sorted(result.missing_keys):
                lines.append(f"    - {key}")

        if result.extra_keys:
            lines.append(_color("  Extra keys:", _YELLOW, use_color=use_color))
            for key in sorted(result.extra_keys):
                lines.append(f"    + {key}")

        if result.mismatched_values:
            lines.append(_color("  Mismatched values:", _RED, use_color=use_color))
            for key, (src_val, tgt_val) in sorted(result.mismatched_values.items()):
                lines.append(f"    ~ {key}")
                lines.append(f"        source : {src_val!r}")
                lines.append(f"        target : {tgt_val!r}")

        lines.append("")

    return "\n".join(lines).rstrip()


def report_multi_comparison_json(
    results: Dict[str, ComparisonResult],
) -> str:
    """Render a JSON multi-environment comparison report.

    Args:
        results: Mapping of target-label -> ComparisonResult.

    Returns:
        A JSON string with one entry per compared environment.
    """
    payload: Dict[str, object] = {}

    for label, result in results.items():
        payload[label] = {
            "has_differences": result.has_differences(),
            "missing_keys": sorted(result.missing_keys),
            "extra_keys": sorted(result.extra_keys),
            "mismatched_values": {
                key: {"source": src, "target": tgt}
                for key, (src, tgt) in sorted(result.mismatched_values.items())
            },
            "summary": result.summary(),
        }

    return json.dumps(payload, indent=2)
