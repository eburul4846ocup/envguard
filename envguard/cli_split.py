"""CLI sub-command: envguard split — split a .env file by key prefix."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.splitter import split_env, write_split


def build_split_parser(subparsers=None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Split a .env file into per-prefix files."
    if subparsers is not None:
        parser = subparsers.add_parser("split", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard split", description=description)

    parser.add_argument("env_file", metavar="ENV_FILE", help="Path to the source .env file.")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory to write split files into (default: current directory).",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        dest="prefixes",
        action="append",
        metavar="PREFIX",
        help="Explicit prefix to split on (repeatable). Auto-detects when omitted.",
    )
    parser.add_argument(
        "--ungrouped-name",
        default=".env.misc",
        metavar="NAME",
        help="Filename for ungrouped keys (default: .env.misc).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without creating files.",
    )
    return parser


def _run_split(args: argparse.Namespace) -> int:
    source = Path(args.env_file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 2

    env = parse_env_file(source)
    result = split_env(env, prefixes=args.prefixes)

    if result.total_keys == 0:
        print("No keys found — nothing to split.")
        return 0

    output_dir = Path(args.output_dir)

    if args.dry_run:
        print(f"Would write {result.file_count} file(s) to '{output_dir}':")
        for group in result.group_names:
            keys = result.groups[group]
            print(f"  .env.{group.lower()}  ({len(keys)} key(s))")
        if result.ungrouped:
            print(f"  {args.ungrouped_name}  ({len(result.ungrouped)} key(s))")
        print(f"Summary: {result.summary()}")
        return 0

    written = write_split(result, output_dir, ungrouped_name=args.ungrouped_name)
    print(f"Wrote {len(written)} file(s) to '{output_dir}':")
    for path in written:
        print(f"  {path}")
    print(f"Summary: {result.summary()}")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_split_parser()
    args = parser.parse_args()
    sys.exit(_run_split(args))


if __name__ == "__main__":  # pragma: no cover
    main()
