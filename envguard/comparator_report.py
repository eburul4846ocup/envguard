"""Cross-environment comparison reporter."""
from __future__ import annotations

import json
from typing import List

from envguard.comparator import ComparisonResult


def _color(code: str, text: str, use_color: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if use_color else text


def report_comparison_text(results: List[ComparisonResult], use_color: bool = True) -> str:
    lines: List[str] = []
    for r in results:
        header = f"=== {r.source} -> {r.target} ==="
        lines.append(header)
        if not r.has_differences():
            lines.append(_color("32", "  No differences.", use_color))
        else:
            for k in sorted(r.missing_in_target):
                lines.append(_color("31", f"  MISSING  {k}", use_color))
            for k in sorted(r.extra_in_target):
                lines.append(_color("33", f"  EXTRA    {k}", use_color))
            for k, (sv, tv) in sorted(r.value_mismatches.items()):
                lines.append(_color("35", f"  MISMATCH {k}: {sv!r} -> {tv!r}", use_color))
        lines.append("")
    return "\n".join(lines).rstrip()


def report_comparison_json(results: List[ComparisonResult]) -> str:
    payload = []
    for r in results:
        payload.append({
            "source": r.source,
            "target": r.target,
            "missing_in_target": sorted(r.missing_in_target),
            "extra_in_target": sorted(r.extra_in_target),
            "value_mismatches": {
                k: {"source": sv, "target": tv}
                for k, (sv, tv) in sorted(r.value_mismatches.items())
            },
        })
    return json.dumps(payload, indent=2)
