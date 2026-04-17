"""CLI sub-command: envguard summarize."""
from __future__ import annotations

import argparse
import json
import sys

from envguard.parser import parse_env_file
from envguard.summarizer import summarize_env


def build_summarize_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Summarize keys in an .env file."
    if sub is not None:
        p = sub.add_parser("summarize", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envguard summarize", description=desc)
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    return p


def _run_summarize(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    result = summarize_env(env)

    if args.fmt == "json":
        print(json.dumps({
            "total_keys": result.total_keys,
            "secret_keys": result.secret_keys,
            "plain_keys": result.plain_keys,
            "empty_keys": result.empty_keys,
        }, indent=2))
    else:
        print(result.summary())
        if result.empty_keys:
            print("\nEmpty keys:")
            for k in result.empty_keys:
                print(f"  - {k}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_summarize_parser()
    args = parser.parse_args()
    sys.exit(_run_summarize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
