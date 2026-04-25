"""CLI entry-point for the `envguard classify` sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.classifier import classify_env
from envguard.parser import parse_env_file


def build_classify_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("classify", help="Classify .env keys by type")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--category",
        default=None,
        help="Show only keys belonging to this category",
    )
    return p


def _run_classify(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = classify_env(env)

    if args.category:
        keys = result.groups.get(args.category, [])
        if args.fmt == "json":
            print(json.dumps({args.category: keys}, indent=2))
        else:
            if not keys:
                print(f"No keys classified as '{args.category}'.")
            else:
                for k in keys:
                    print(f"  {k}")
        return 0

    if args.fmt == "json":
        print(json.dumps({"summary": result.summary(), "groups": result.groups}, indent=2))
    else:
        print(result.summary())
        for category in result.group_names:
            print(f"\n[{category}]")
            for k in result.groups[category]:
                print(f"  {k}")

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-classify")
    sub = parser.add_subparsers(dest="command")
    build_classify_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_classify(args))
