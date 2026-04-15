"""CLI sub-command: envguard redact — print a .env file with secrets masked."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.redactor import redact_env


def build_redact_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "redact",
        help="Print a .env file with sensitive values masked.",
    )
    p.add_argument("file", help="Path to the .env file to redact.")
    p.add_argument(
        "--mask",
        default="***",
        help="Replacement string for sensitive values (default: ***).",
    )
    p.add_argument(
        "--extra-keys",
        nargs="*",
        metavar="KEY",
        default=[],
        help="Additional key names to always redact.",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        help="Print a redaction summary to stderr.",
    )
    return p


def _run_redact(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = redact_env(env, mask=args.mask, extra_keys=set(args.extra_keys))

    if args.format == "json":
        print(json.dumps(result.redacted, indent=2, sort_keys=True))
    else:
        for key, value in sorted(result.redacted.items()):
            print(f"{key}={value}")

    if args.summary:
        print(result.summary(), file=sys.stderr)

    return 0
