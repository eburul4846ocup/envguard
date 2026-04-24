"""Reporters for MultiEnvDiff results (text and JSON)."""
from __future__ import annotations

import json
from typing import List

from envguard.differ_env import MultiEnvDiff, EnvKeyReport

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"


def _color(text: str, code: str, use_color: bool) -> str:
    return f"{code}{text}{_RESET}" if use_color else text


def report_multi_diff_text(diff: MultiEnvDiff, use_color: bool = False) -> str:
    lines: List[str] = []
    header = f"Environments: {', '.join(diff.env_names)}"
    lines.append(header)
    lines.append("-" * len(header))

    if not diff.has_issues:
        lines.append(_color("All keys consistent across environments.", _GREEN, use_color))
        return "\n".join(lines)

    if diff.keys_with_gaps:
        lines.append("Keys missing in some environments:")
        for r in diff.keys_with_gaps:
            missing = ", ".join(r.missing_in)
            lines.append(
                f"  {_color(r.key, _YELLOW, use_color)} — missing in: {missing}"
            )

    if diff.inconsistent_keys:
        lines.append("Keys with differing values:")
        for r in diff.inconsistent_keys:
            lines.append(f"  {_color(r.key, _RED, use_color)}")
            for env_name, val in r.values.items():
                display = repr(val) if val is not None else "<absent>"
                lines.append(f"    {env_name}: {display}")

    lines.append("")
    lines.append(diff.summary())
    return "\n".join(lines)


def report_multi_diff_json(diff: MultiEnvDiff) -> str:
    payload = {
        "environments": diff.env_names,
        "has_issues": diff.has_issues,
        "summary": diff.summary(),
        "keys_with_gaps": [
            {"key": r.key, "missing_in": r.missing_in}
            for r in diff.keys_with_gaps
        ],
        "inconsistent_keys": [
            {"key": r.key, "values": {k: v for k, v in r.values.items()}}
            for r in diff.inconsistent_keys
        ],
    }
    return json.dumps(payload, indent=2)
