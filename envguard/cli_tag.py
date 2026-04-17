"""CLI interface for the tagger module."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.tagger import tag_env


def build_tag_parser(sub=None):
    kwargs = dict(
        description="Tag env keys with labels based on prefix or substring rules."
    )
    p = sub.add_parser("tag", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--rule",
        metavar="TAG:PREFIX",
        action="append",
        default=[],
        dest="rules",
        help="Tagging rule in TAG:PREFIX format (repeatable)",
    )
    p.add_argument(
        "--mode",
        choices=["prefix", "contains"],
        default="prefix",
        help="Matching mode (default: prefix)",
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")
    return p


def _run_tag(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)

    rules: dict[str, list[str]] = {}
    for rule in args.rules:
        if ":" not in rule:
            print(f"error: invalid rule '{rule}', expected TAG:PREFIX", file=sys.stderr)
            return 2
        tag, pattern = rule.split(":", 1)
        rules.setdefault(tag, []).append(pattern)

    result = tag_env(env, rules, match_mode=args.mode)

    if args.json:
        print(json.dumps({"tags": result.tags, "untagged": result.untagged}, indent=2))
    else:
        print(f"Summary: {result.summary()}")
        for tag in result.tag_names:
            keys = result.tags[tag]
            print(f"  [{tag}] {', '.join(keys) if keys else '(none)'}")
        if result.untagged:
            print(f"  [untagged] {', '.join(result.untagged)}")

    return 0


def main():
    p = build_tag_parser()
    sys.exit(_run_tag(p.parse_args()))


if __name__ == "__main__":
    main()
