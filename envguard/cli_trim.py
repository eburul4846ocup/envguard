"""cli_trim.py – CLI wrapper for the trimmer feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.trimmer import trim_env


def build_trim_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envguard trim",
        description="Strip leading/trailing whitespace from .env values.",
    )
    if parent is not None:
        parser = parent.add_parser("trim", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the .env file to trim.")
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the source file with trimmed output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress summary output.",
    )
    return parser


def _run_trim(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = trim_env(env)

    if not args.quiet:
        print(result.summary())

    if args.in_place:
        path.write_text(result.to_string(), encoding="utf-8")
    else:
        print(result.to_string(), end="")

    return 1 if result.is_changed else 0


def main() -> None:  # pragma: no cover
    parser = build_trim_parser()
    args = parser.parse_args()
    sys.exit(_run_trim(args))


if __name__ == "__main__":  # pragma: no cover
    main()
