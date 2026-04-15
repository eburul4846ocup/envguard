"""CLI sub-command: envguard profile <file>"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.profiler import profile_env


def build_profile_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "profile",
        help="Summarise and categorise variables in an .env file",
    )
    p.add_argument("file", type=Path, help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_run_profile)


def _run_profile(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    result = profile_env(env)
    summary = result.summary()

    if args.fmt == "json":
        data = {
            "summary": summary,
            "categories": {
                "empty": result.empty_values,
                "secrets": result.secret_keys,
                "urls": result.url_values,
                "booleans": result.boolean_values,
                "numeric": result.numeric_values,
                "plain": result.plain_values,
            },
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Profile: {args.file}")
        print(f"  Total keys   : {summary['total']}")
        print(f"  Empty values : {summary['empty']}")
        print(f"  Secrets      : {summary['secrets']}")
        print(f"  URLs         : {summary['urls']}")
        print(f"  Booleans     : {summary['booleans']}")
        print(f"  Numeric      : {summary['numeric']}")
        print(f"  Plain text   : {summary['plain']}")

    return 0
