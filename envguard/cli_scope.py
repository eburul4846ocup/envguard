"""CLI entry-point for the `envguard scope` sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.scoper import scope_env


def build_scope_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "scope",
        help="Extract a subset of env vars by prefix or key list.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--prefix",
        default=None,
        help="Include only keys that start with this prefix.",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        default=None,
        metavar="KEY",
        help="Include only these specific keys (space-separated).",
    )
    p.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove the prefix from output key names.",
    )
    p.add_argument(
        "--case-insensitive",
        action="store_true",
        default=False,
        help="Match prefix/keys case-insensitively.",
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv).",
    )
    return p


def _run_scope(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = scope_env(
        env,
        prefix=args.prefix,
        keys=args.keys,
        case_sensitive=not args.case_insensitive,
    )

    if args.fmt == "json":
        print(json.dumps(result.scoped, indent=2, sort_keys=True))
    else:
        output = result.to_string(strip_prefix=args.strip_prefix)
        if output:
            print(output)

    print(result.summary(), file=sys.stderr)
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-scope")
    sub = parser.add_subparsers(dest="command")
    build_scope_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_scope(args))
