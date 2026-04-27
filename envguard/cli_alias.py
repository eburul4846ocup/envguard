"""CLI entry-point for the *alias* sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.aliaser import alias_env
from envguard.parser import parse_env_file


def build_alias_parser(parent: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:  # noqa: F821
    kwargs = dict(
        description="Rename env keys using an alias map.",
    )
    if parent is not None:
        parser = parent.add_parser("alias", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envguard alias", **kwargs)

    parser.add_argument("file", help="Path to the .env file to process.")
    parser.add_argument(
        "--alias",
        metavar="NEW=OLD",
        action="append",
        default=[],
        dest="aliases",
        help="Alias mapping NEW_KEY=OLD_KEY (repeatable).",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        default=False,
        help="Retain the source key alongside the alias.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Write the result back to the source file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="as_json",
        help="Output result as JSON.",
    )
    return parser


def _parse_aliases(raw: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            print(f"[error] Invalid alias spec (expected NEW=OLD): {item!r}", file=sys.stderr)
            sys.exit(2)
        new, old = item.split("=", 1)
        aliases[new.strip()] = old.strip()
    return aliases


def _run_alias(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    aliases = _parse_aliases(args.aliases)
    result = alias_env(env, aliases, keep_original=args.keep_original)

    if args.as_json:
        print(json.dumps({"env": result.env, "applied": result.applied,
                          "skipped": result.skipped, "removed": result.removed}, indent=2))
    else:
        print(f"envguard alias: {result.summary()}")
        if result.applied:
            for key in result.applied:
                print(f"  ~ {key}")

    if args.in_place:
        path.write_text(result.to_string())

    return 0 if result.is_changed or not aliases else 0


def main(argv: list[str] | None = None) -> None:
    parser = build_alias_parser()
    args = parser.parse_args(argv)
    sys.exit(_run_alias(args))


if __name__ == "__main__":  # pragma: no cover
    main()
