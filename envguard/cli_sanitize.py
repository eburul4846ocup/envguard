"""CLI entry point for the `sanitize` subcommand."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.sanitizer import sanitize_env


def build_sanitize_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "sanitize",
        help="Sanitize .env values (strip null bytes, control chars, etc.)",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--no-strip-null",
        dest="strip_null",
        action="store_false",
        default=True,
        help="Disable null-byte stripping",
    )
    p.add_argument(
        "--no-strip-ctrl",
        dest="strip_ctrl",
        action="store_false",
        default=True,
        help="Disable control-character stripping",
    )
    p.add_argument(
        "--collapse-spaces",
        action="store_true",
        default=False,
        help="Collapse consecutive spaces into one",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write sanitized output back to the file",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress output; only use exit code",
    )
    return p


def _run_sanitize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = sanitize_env(
        env,
        strip_null=args.strip_null,
        strip_ctrl=args.strip_ctrl,
        collapse_spaces=args.collapse_spaces,
    )

    if not args.quiet:
        print(result.summary())

    if result.is_changed:
        if args.in_place:
            path.write_text(result.to_string() + "\n", encoding="utf-8")
            if not args.quiet:
                print(f"Written sanitized output to {path}")
        return 1

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-sanitize")
    sub = parser.add_subparsers(dest="command")
    build_sanitize_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_sanitize(args))
