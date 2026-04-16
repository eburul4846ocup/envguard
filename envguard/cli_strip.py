"""CLI sub-command: envguard strip."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.stripper import strip_env


def build_strip_parser(subparsers=None):
    kwargs = dict(
        description="Strip comments and blank lines from a .env file."
    )
    if subparsers is None:
        parser = argparse.ArgumentParser(**kwargs)
    else:
        parser = subparsers.add_parser("strip", **kwargs)

    parser.add_argument("file", type=Path, help="Path to .env file")
    parser.add_argument(
        "--keep-comments", action="store_true", help="Preserve comment lines"
    )
    parser.add_argument(
        "--keep-blanks", action="store_true", help="Preserve blank lines"
    )
    parser.add_argument(
        "--in-place", "-i", action="store_true", help="Write result back to file"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress summary output"
    )
    return parser


def _run_strip(args) -> int:
    path: Path = args.file
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    result = strip_env(
        path,
        keep_comments=args.keep_comments,
        keep_blanks=args.keep_blanks,
    )

    if not args.quiet:
        print(result.summary())

    if args.in_place:
        path.write_text(result.to_string(), encoding="utf-8")
    else:
        print(result.to_string(), end="")

    return 0


def main():
    parser = build_strip_parser()
    sys.exit(_run_strip(parser.parse_args()))


if __name__ == "__main__":
    main()
