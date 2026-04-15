"""CLI sub-command: envguard sort — reorder .env keys and emit the result."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.sorter import SortOrder, sort_env


def build_sort_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Sort keys in a .env file and print the result."
    if subparsers is not None:
        parser = subparsers.add_parser("sort", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard sort", description=description)

    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument(
        "--order",
        choices=[o.value for o in SortOrder],
        default=SortOrder.ALPHA.value,
        help="Sort order (default: alpha).",
    )
    parser.add_argument(
        "--group-prefixes",
        metavar="PREFIX",
        nargs="+",
        default=[],
        help="Ordered list of key prefixes used with --order=group.",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a one-line summary to stderr instead of the sorted file.",
    )
    return parser


def _run_sort(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    order = SortOrder(args.order)
    result = sort_env(env, order=order, group_prefixes=args.group_prefixes)

    if args.summary:
        print(result.summary(), file=sys.stderr)
        return 0

    if args.fmt == "json":
        print(json.dumps(result.sorted_env, indent=2))
    else:
        for key, value in result.sorted_env.items():
            needs_quotes = " " in value or "#" in value
            if needs_quotes:
                print(f'{key}="{value}"')
            else:
                print(f"{key}={value}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_sort_parser()
    args = parser.parse_args()
    sys.exit(_run_sort(args))


if __name__ == "__main__":  # pragma: no cover
    main()
