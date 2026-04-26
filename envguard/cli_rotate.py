"""CLI sub-command: envguard rotate — check secret key rotation policy."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.rotator import rotate_env


def build_rotate_parser(sub=None):
    kwargs = dict(
        description="Check secret keys against a rotation policy."
    )
    if sub is not None:
        p = sub.add_parser("rotate", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="envguard rotate", **kwargs)

    p.add_argument("env_file", help="Path to .env file to inspect.")
    p.add_argument(
        "--pins",
        metavar="FILE",
        help="JSON file mapping key names to ISO pin dates (YYYY-MM-DD).",
    )
    p.add_argument(
        "--max-age",
        type=int,
        default=90,
        metavar="DAYS",
        help="Maximum allowed age in days before a key is flagged (default: 90).",
    )
    p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output results as JSON.",
    )
    return p


def _run_rotate(args) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)

    pin_dates: dict = {}
    if args.pins:
        pins_path = Path(args.pins)
        if not pins_path.exists():
            print(f"error: pins file not found: {pins_path}", file=sys.stderr)
            return 2
        with pins_path.open() as fh:
            pin_dates = json.load(fh)

    result = rotate_env(env, pin_dates=pin_dates, max_age_days=args.max_age)

    if getattr(args, "json_output", False):
        payload = {
            "is_clean": result.is_clean,
            "checked": result.checked,
            "issue_count": result.issue_count,
            "issues": [
                {
                    "key": i.key,
                    "pinned_date": i.pinned_date.isoformat() if i.pinned_date else None,
                    "age_days": i.age_days,
                    "reason": i.reason,
                }
                for i in result.issues
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.summary())
        for issue in result.issues:
            print(f"  WARN  {issue}")

    return 0 if result.is_clean else 1


def main():
    parser = build_rotate_parser()
    args = parser.parse_args()
    sys.exit(_run_rotate(args))


if __name__ == "__main__":
    main()
