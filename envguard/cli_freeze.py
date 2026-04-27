"""cli_freeze.py – CLI sub-commands: freeze (save) and thaw (compare)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.freezer import freeze_env, thaw_env, FreezeResult
from envguard.parser import parse_env_file


def build_freeze_parser(sub: "argparse._SubParsersAction") -> None:  # type: ignore[type-arg]
    p = sub.add_parser("freeze", help="Freeze an .env file to a JSON record.")
    p.add_argument("env_file", type=Path, help="Source .env file")
    p.add_argument("--output", "-o", type=Path, default=None, help="Destination JSON file")
    p.set_defaults(func=_run_freeze)

    t = sub.add_parser("thaw", help="Detect drift between a frozen record and a live .env.")
    t.add_argument("freeze_file", type=Path, help="Previously saved freeze JSON")
    t.add_argument("env_file", type=Path, help="Current .env file to compare")
    t.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    t.set_defaults(func=_run_thaw)


def _run_freeze(args: argparse.Namespace) -> int:
    if not args.env_file.exists():
        print(f"error: file not found: {args.env_file}", file=sys.stderr)
        return 2
    env = parse_env_file(args.env_file)
    result = freeze_env(env)
    dest = args.output or args.env_file.with_suffix(".freeze.json")
    result.save(dest)
    print(f"Frozen {result.key_count} key(s) → {dest}")
    return 0


def _run_thaw(args: argparse.Namespace) -> int:
    for p in (args.freeze_file, args.env_file):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
    frozen = FreezeResult.load(args.freeze_file)
    current = parse_env_file(args.env_file)
    result = thaw_env(frozen, current)
    if getattr(args, "as_json", False):
        print(json.dumps({
            "has_drift": result.has_drift,
            "added": result.added,
            "removed": result.removed,
            "changed": result.changed,
        }, indent=2))
    else:
        print(result.summary())
        for k in result.added:
            print(f"  + {k}")
        for k in result.removed:
            print(f"  - {k}")
        for k in result.changed:
            print(f"  ~ {k}")
    return 1 if result.has_drift else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="envguard-freeze")
    sub = parser.add_subparsers(dest="command")
    build_freeze_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
