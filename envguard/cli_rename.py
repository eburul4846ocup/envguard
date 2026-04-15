"""CLI sub-command: envguard rename — rename keys in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.renamer import rename_env
from envguard.exporter import export_dotenv


def build_rename_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "rename",
        help="Rename one or more keys in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file to process.")
    p.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        dest="renames",
        required=True,
        help="Key rename pair (repeatable). Example: --rename OLD_KEY=NEW_KEY",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the source file with renamed keys.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would change without writing anything.",
    )
    return p


def _run_rename(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)

    mapping: dict[str, str] = {}
    for pair in args.renames:
        if "=" not in pair:
            print(f"[error] Invalid rename pair (expected OLD=NEW): {pair}", file=sys.stderr)
            return 2
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()

    result = rename_env(env, mapping)

    print(result.summary())

    if result.skipped:
        print("[warn] Some keys were not found and could not be renamed.", file=sys.stderr)

    if args.dry_run:
        print("[dry-run] No changes written.")
        return 0

    if args.in_place:
        path.write_text(export_dotenv(result.renamed))
        print(f"[ok] Written to {path}")
    else:
        print(export_dotenv(result.renamed))

    return 0 if not result.skipped else 1
