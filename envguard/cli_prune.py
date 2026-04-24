"""cli_prune.py — CLI sub-command: envguard prune"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.pruner import prune_env


def build_prune_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    description = "Remove keys from a .env file by name or regex pattern."
    if sub is not None:
        parser = sub.add_parser("prune", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard prune", description=description)

    parser.add_argument("file", help="Path to the .env file to prune.")
    parser.add_argument(
        "-k", "--key",
        dest="keys",
        metavar="KEY",
        action="append",
        default=[],
        help="Exact key name to remove (repeatable).",
    )
    parser.add_argument(
        "-p", "--pattern",
        dest="patterns",
        metavar="REGEX",
        action="append",
        default=[],
        help="Full-match regex; every matching key is removed (repeatable).",
    )
    parser.add_argument(
        "--in-place", "-i",
        action="store_true",
        help="Overwrite the source file with the pruned result.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress informational output.",
    )
    return parser


def _run_prune(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = prune_env(env, keys=args.keys, patterns=args.patterns)

    if not args.quiet:
        print(result.summary())

    if args.in_place:
        path.write_text(result.to_string(), encoding="utf-8")
    else:
        sys.stdout.write(result.to_string())

    return 1 if result.is_changed else 0


def main() -> None:  # pragma: no cover
    parser = build_prune_parser()
    sys.exit(_run_prune(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
