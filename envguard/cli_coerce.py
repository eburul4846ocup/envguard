"""CLI sub-command: envguard coerce — display inferred types for .env values."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.coercer import coerce_env
from envguard.parser import parse_env_file


def build_coerce_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("coerce", help="Infer and display Python types for .env values.")
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--only-changed",
        action="store_true",
        help="Only show keys whose value was coerced away from string.",
    )
    return p


def _run_coerce(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = coerce_env(env)

    if args.fmt == "json":
        payload = {
            key: {"value": result.coerced[key], "type": result.type_map[key]}
            for key in sorted(result.coerced)
            if not args.only_changed or result.type_map[key] != "str"
        }
        print(json.dumps(payload, indent=2))
    else:
        shown = False
        for key in sorted(result.coerced):
            if args.only_changed and result.type_map[key] == "str":
                continue
            print(f"{key}={result.coerced[key]!r}  # {result.type_map[key]}")
            shown = True
        if not shown:
            print("All values remain as strings.")
        print()
        print(result.summary())

    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-coerce")
    sub = parser.add_subparsers(dest="command")
    build_coerce_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_coerce(args))
