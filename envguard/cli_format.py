"""CLI sub-command: envguard format."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.formatter import format_env


def build_format_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Format a .env file with consistent style."
    if sub is not None:
        p = sub.add_parser("format", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envguard format", description=desc)
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--quote", action="store_true", help="Wrap all values in double quotes")
    p.add_argument("--sort", action="store_true", help="Sort keys alphabetically")
    p.add_argument("--write", action="store_true", help="Write formatted output back to file")
    p.add_argument("--check", action="store_true", help="Exit 1 if file would be reformatted")
    return p


def _run_format(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    original_lines = path.read_text().splitlines(keepends=True)
    result = format_env(env, quote_values=args.quote, sort_keys=args.sort, original_lines=original_lines)

    if args.check:
        if result.is_changed:
            print(f"[format] {path} would be reformatted.")
            return 1
        print(f"[format] {path} is already formatted.")
        return 0

    if args.write:
        path.write_text(result.to_string())
        print(f"[format] {path}: {result.summary()}")
    else:
        print(result.to_string(), end="")

    return 0


def main() -> None:
    parser = build_format_parser()
    args = parser.parse_args()
    sys.exit(_run_format(args))


if __name__ == "__main__":
    main()
