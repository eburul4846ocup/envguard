"""CLI sub-command: envguard flatten."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.flattener import flatten_env


def build_flatten_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "flatten",
        help="Replace dotted (or custom) key separators with a flat delimiter.",
    )
    p.add_argument("file", help="Path to the .env file to flatten.")
    p.add_argument(
        "--from-sep",
        default=".",
        metavar="SEP",
        help="Separator to replace (default: '.').",
    )
    p.add_argument(
        "--to-sep",
        default="_",
        metavar="SEP",
        help="Replacement separator (default: '_').",
    )
    p.add_argument(
        "--no-uppercase",
        action="store_true",
        default=False,
        help="Do not uppercase keys after flattening.",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the source file with the flattened output.",
    )
    return p


def _run_flatten(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = flatten_env(
        env,
        from_sep=args.from_sep,
        to_sep=args.to_sep,
        uppercase=not args.no_uppercase,
    )

    print(result.summary())

    if result.is_changed:
        output = result.to_string()
        if args.in_place:
            path.write_text(output + "\n", encoding="utf-8")
            print(f"Written to {path}")
        else:
            print(output)
        return 1  # non-zero signals changes were made

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-flatten")
    sub = parser.add_subparsers(dest="command")
    build_flatten_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_flatten(args))
