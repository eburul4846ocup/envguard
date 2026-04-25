"""CLI sub-command: resolve — merge and expand variable references across .env files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.resolver import resolve_envs


def build_resolve_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "resolve",
        help="Merge and expand ${VAR} references across one or more .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files in merge order (first = base, last = highest priority).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any unresolved references remain.",
    )
    return p


def _run_resolve(args: argparse.Namespace) -> int:
    layers = []
    for path_str in args.files:
        path = Path(path_str)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        layers.append(parse_env_file(path))

    result = resolve_envs(layers)

    if args.format == "json":
        payload = {
            "resolved": result.resolved,
            "unresolved_refs": result.unresolved_refs,
            "is_clean": result.is_clean,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())
        if result.resolved:
            print()
            for key, val in sorted(result.resolved.items()):
                marker = " [!]" if key in result.unresolved_refs else ""
                print(f"  {key}={val}{marker}")
        if not result.is_clean:
            print()
            print("Unresolved references:")
            for key, refs in sorted(result.unresolved_refs.items()):
                print(f"  {key}: {', '.join(refs)}")

    if args.strict and not result.is_clean:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-resolve")
    sub = parser.add_subparsers(dest="command")
    build_resolve_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_resolve(args))
