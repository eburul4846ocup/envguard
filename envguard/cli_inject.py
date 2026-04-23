"""CLI sub-command: envguard inject — inject .env variables into a shell export block."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from envguard.injector import inject_env
from envguard.parser import parse_env_file


def build_inject_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "inject",
        help="Inject variables from a .env file into the current environment or a target file.",
    )
    p.add_argument("source", help="Source .env file whose variables will be injected.")
    p.add_argument(
        "--target",
        metavar="FILE",
        help="Optional target .env file.  If omitted, os.environ is used as the target.",
    )
    p.add_argument(
        "--override",
        action="store_true",
        default=False,
        help="Overwrite variables that already exist in the target.",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Limit injection to these specific keys.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.set_defaults(func=_run_inject)
    return p


def _run_inject(args: argparse.Namespace) -> int:
    try:
        source_vars = parse_env_file(args.source)
    except FileNotFoundError:
        print(f"error: source file not found: {args.source}", file=sys.stderr)
        return 2

    if args.target:
        try:
            target_vars = parse_env_file(args.target)
        except FileNotFoundError:
            print(f"error: target file not found: {args.target}", file=sys.stderr)
            return 2
    else:
        target_vars = dict(os.environ)

    result = inject_env(
        source_vars,
        target=target_vars,
        override=args.override,
        keys=args.keys,
    )

    if args.fmt == "json":
        print(
            json.dumps(
                {
                    "injected": result.injected,
                    "skipped": list(result.skipped.keys()),
                    "overridden": result.overridden,
                    "summary": result.summary(),
                },
                indent=2,
            )
        )
    else:
        print(f"Summary: {result.summary()}")
        if result.injected:
            print("  Injected:")
            for k, v in sorted(result.injected.items()):
                print(f"    {k}={v}")
        if result.overridden:
            print("  Overridden:")
            for k, v in sorted(result.overridden.items()):
                print(f"    {k}={v}")
        if result.skipped:
            print("  Skipped (already exist):")
            for k in sorted(result.skipped):
                print(f"    {k}")

    return 0 if result.is_changed or not source_vars else 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-inject")
    sub = parser.add_subparsers()
    build_inject_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))
