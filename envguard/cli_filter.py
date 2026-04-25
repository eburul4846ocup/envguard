"""CLI sub-command: envguard filter — filter .env keys by prefix or pattern."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.filterer import filter_env
from envguard.parser import parse_env_file


def build_filter_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("filter", help="Filter .env keys by prefix or regex pattern.")
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--prefix",
        dest="prefixes",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Include keys starting with PREFIX (repeatable).",
    )
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="REGEX",
        help="Include keys matching REGEX (repeatable).",
    )
    p.add_argument(
        "--exclude-empty",
        action="store_true",
        default=False,
        help="Exclude keys with empty values.",
    )
    p.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert the filter (show excluded keys instead).",
    )
    p.add_argument(
        "--json",
        dest="use_json",
        action="store_true",
        default=False,
        help="Output as JSON.",
    )
    return p


def _run_filter(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = filter_env(
        env,
        prefixes=args.prefixes or None,
        patterns=args.patterns or None,
        exclude_empty=args.exclude_empty,
        invert=args.invert,
    )

    if args.use_json:
        print(json.dumps({"matched": result.matched, "excluded": result.excluded}, indent=2))
    else:
        print(result.summary())
        for key, value in sorted(result.matched.items()):
            print(f"  {key}={value}")

    return 0 if not result.is_empty else 1


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-filter")
    sub = parser.add_subparsers(dest="command")
    build_filter_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_filter(args))
