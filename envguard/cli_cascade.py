"""CLI sub-command: envguard cascade

Cascade two or more .env files, printing the merged result and a summary
of which keys were overridden.

Usage examples
--------------
  envguard cascade .env .env.local
  envguard cascade .env .env.staging .env.local --json
  envguard cascade .env .env.local --show-provenance
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envguard.cascader import cascade_envs
from envguard.parser import parse_env_file


def build_cascade_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "cascade",
        help="Merge .env files left-to-right; later files override earlier ones.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to cascade (base first).",
    )
    p.add_argument(
        "--json",
        dest="use_json",
        action="store_true",
        help="Emit merged env as JSON.",
    )
    p.add_argument(
        "--show-provenance",
        action="store_true",
        help="Print the override chain for each key.",
    )
    p.set_defaults(func=_run_cascade)
    return p


def _run_cascade(args: argparse.Namespace) -> int:
    layers = []
    for path in args.files:
        try:
            layers.append(parse_env_file(path))
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    result = cascade_envs(layers)

    if args.use_json:
        print(json.dumps(result.merged, indent=2))
        return 0

    # Text output
    print(result.summary())

    if result.overridden_keys:
        print("\nOverridden keys:")
        for key in result.overridden_keys:
            chain = result.provenance[key]
            chain_str = " -> ".join(f"[{i}]{v}" for i, v in chain)
            print(f"  {key}: {chain_str}")

    if args.show_provenance:
        print("\nFull provenance:")
        for key in sorted(result.merged):
            chain = result.provenance[key]
            chain_str = " -> ".join(f"[layer {i}] {v!r}" for i, v in chain)
            print(f"  {key}: {chain_str}")

    return 0


def main(argv: List[str] | None = None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-cascade")
    sub = parser.add_subparsers()
    build_cascade_parser(sub)
    args = parser.parse_args(argv)
    sys.exit(args.func(args) if hasattr(args, "func") else 0)
