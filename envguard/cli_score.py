"""CLI entry-point for the `envguard score` sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.scorer import score_env


def build_score_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("score", help="Score an .env file on a 0-100 quality scale")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-require-uppercase",
        action="store_false",
        dest="require_uppercase",
        default=True,
        help="Disable penalty for lowercase key names",
    )
    p.add_argument(
        "--fail-below",
        type=int,
        default=0,
        metavar="N",
        help="Exit 1 if score is below N (default: 0 = never fail on score)",
    )
    return p


def _run_score(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = score_env(env, require_uppercase=args.require_uppercase)

    if args.fmt == "json":
        print(
            json.dumps(
                {
                    "score": result.score,
                    "grade": result.grade,
                    "total_keys": result.total_keys,
                    "penalties": result.penalties,
                }
            )
        )
    else:
        print(result.summary())
        if result.penalties:
            print("Penalties:")
            for p in result.penalties:
                print(f"  - {p}")

    if args.fail_below and result.score < args.fail_below:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envguard-score")
    sub = parser.add_subparsers(dest="command")
    build_score_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_score(args))
