"""CLI sub-command: envguard merge — merge multiple .env files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envguard.exporter import export_env, ExportFormat
from envguard.merger import MergeError, MergeStrategy, merge_envs
from envguard.parser import parse_env_file


def build_merge_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "merge",
        help="Merge multiple .env files into one, detecting conflicts.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to merge (in order).",
    )
    p.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.LAST_WINS.value,
        help="Conflict resolution strategy (default: last-wins).",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.DOTENV.value,
        help="Output format (default: dotenv).",
    )
    p.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of stdout.",
    )
    p.add_argument(
        "--show-conflicts",
        action="store_true",
        help="Print conflict details to stderr even when not using strict mode.",
    )
    p.set_defaults(func=_run_merge)


def _run_merge(args: argparse.Namespace) -> int:
    strategy = MergeStrategy(args.strategy)
    sources = []
    for path_str in args.files:
        path = Path(path_str)
        if not path.exists():
            print(f"envguard merge: file not found: {path}", file=sys.stderr)
            return 2
        sources.append((str(path), parse_env_file(path)))

    try:
        result = merge_envs(sources, strategy=strategy)
    except MergeError as exc:
        print(f"envguard merge: {exc}", file=sys.stderr)
        return 1

    if args.show_conflicts and result.has_conflicts:
        for conflict in result.conflicts:
            print(f"  CONFLICT: {conflict}", file=sys.stderr)

    fmt = ExportFormat(args.fmt)
    output_text = export_env(result.merged, fmt)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        print(output_text, end="")

    return 1 if result.has_conflicts else 0
