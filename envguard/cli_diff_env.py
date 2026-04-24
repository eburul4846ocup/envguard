"""CLI sub-command: envguard diff-env — diff keys across multiple .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.differ_env import diff_many
from envguard.diff_env_reporter import report_multi_diff_text, report_multi_diff_json


def build_diff_env_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Diff key presence and values across multiple .env files."
    if subparsers is not None:
        parser = subparsers.add_parser("diff-env", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envguard diff-env", description=desc)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="NAME=FILE",
        help="Named env files in NAME=FILE format (e.g. dev=.env.dev prod=.env.prod)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI colour output (text format only)",
    )
    return parser


def _run_diff_env(args: argparse.Namespace) -> int:
    env_paths = {}
    for spec in args.files:
        if "=" not in spec:
            print(f"error: expected NAME=FILE, got {spec!r}", file=sys.stderr)
            return 2
        name, _, path_str = spec.partition("=")
        p = Path(path_str)
        if not p.exists():
            print(f"error: file not found: {path_str}", file=sys.stderr)
            return 2
        env_paths[name] = p

    if len(env_paths) < 2:
        print("error: at least two NAME=FILE entries are required.", file=sys.stderr)
        return 2

    diff = diff_many(env_paths)

    if args.fmt == "json":
        print(report_multi_diff_json(diff))
    else:
        print(report_multi_diff_text(diff, use_color=args.color))

    return 1 if diff.has_issues else 0


def main() -> None:  # pragma: no cover
    parser = build_diff_env_parser()
    args = parser.parse_args()
    sys.exit(_run_diff_env(args))


if __name__ == "__main__":  # pragma: no cover
    main()
