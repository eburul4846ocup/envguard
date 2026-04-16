"""CLI entry point for the format sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.formatter import format_env
from envguard.parser import parse_env_file


def build_format_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # noqa: SLF001
    p = sub.add_parser("format", help="Format a .env file in-place or to stdout")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--quote-values",
        action="store_true",
        default=False,
        help="Wrap all values in double quotes",
    )
    p.add_argument(
        "--sort",
        action="store_true",
        default=False,
        help="Sort keys alphabetically",
    )
    p.add_argument(
        "--in-place",
        "-i",
        action="store_true",
        default=False,
        help="Write formatted output back to the file",
    )
    p.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Exit with code 1 if the file would be changed (useful in CI)",
    )
    p.set_defaults(func=_run_format)
    return p


def _run_format(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = format_env(env, quote_values=args.quote_values, sort_keys=args.sort)

    if args.check:
        if result.is_changed:
            print(f"would reformat {path}")
            return 1
        print(f"{path} already formatted")
        return 0

    if args.in_place:
        path.write_text(result.to_string(), encoding="utf-8")
        if result.is_changed:
            print(f"reformatted {path}")
        else:
            print(f"{path} unchanged")
    else:
        print(result.to_string(), end="")

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-format")
    sub = parser.add_subparsers()
    build_format_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
