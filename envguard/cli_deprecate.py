"""CLI sub-command: envguard deprecate — check for deprecated keys."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.deprecator import check_deprecations


def build_deprecate_parser(sub=None):
    kwargs = dict(
        description="Check .env file for deprecated keys."
    )
    if sub is not None:
        p = sub.add_parser("deprecate", **kwargs)
    else:
        p = argparse.ArgumentParser(**kwargs)
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--map",
        metavar="OLD:NEW",
        action="append",
        default=[],
        help="Deprecated key mapping (e.g. OLD_KEY:NEW_KEY). Repeat for multiple.",
    )
    p.add_argument(
        "--map-no-replacement",
        metavar="KEY",
        action="append",
        default=[],
        dest="no_replacement",
        help="Deprecated key with no replacement.",
    )
    p.add_argument("--json", action="store_true", dest="json_out", help="JSON output")
    return p


def _run_deprecate(args) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)

    dep_map = {}
    for entry in args.map:
        if ":" in entry:
            old, new = entry.split(":", 1)
            dep_map[old.strip()] = new.strip()
    for key in args.no_replacement:
        dep_map[key.strip()] = None

    result = check_deprecations(env, dep_map)

    if args.json_out:
        print(json.dumps({
            "is_clean": result.is_clean,
            "checked": result.checked,
            "issues": [
                {"key": i.key, "replacement": i.replacement}
                for i in result.issues
            ],
        }))
    else:
        print(result.summary())
        for issue in result.issues:
            print(f"  {issue}")

    return 0 if result.is_clean else 1


def main():
    parser = build_deprecate_parser()
    sys.exit(_run_deprecate(parser.parse_args()))


if __name__ == "__main__":
    main()
