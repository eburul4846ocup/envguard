"""CLI sub-command: envguard group — display grouped env keys."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envguard.grouper import group_env
from envguard.parser import parse_env_file


def build_group_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Group .env keys by prefix for organised review."
    if subparsers is not None:
        parser = subparsers.add_parser("group", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard group", description=description)

    parser.add_argument("file", help="Path to the .env file to group.")
    parser.add_argument(
        "--prefixes",
        nargs="+",
        metavar="PREFIX",
        default=None,
        help="Explicit prefixes to group by (e.g. DB REDIS APP).",
    )
    parser.add_argument(
        "--separator",
        default="_",
        help="Separator character between prefix and key name (default: '_').",
    )
    parser.add_argument(
        "--min-prefix-length",
        type=int,
        default=2,
        metavar="N",
        help="Minimum prefix length to form a group (default: 2).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    return parser


def _run_group(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    result = group_env(
        env,
        separator=args.separator,
        min_prefix_length=args.min_prefix_length,
        known_prefixes=args.prefixes,
    )

    if args.output_format == "json":
        payload = {
            "groups": {k: list(v.keys()) for k, v in result.groups.items()},
            "ungrouped": list(result.ungrouped.keys()),
            "total_keys": result.total_keys,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_group_parser()
    args = parser.parse_args(argv)
    return _run_group(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
