"""CLI sub-command: envguard compare."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.multi_comparator import compare_many
from envguard.comparator_report import report_comparison_text, report_comparison_json


def build_compare_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("compare", help="Compare a baseline .env against one or more targets")
    p.add_argument("baseline", type=Path, help="Baseline .env file")
    p.add_argument("targets", type=Path, nargs="+", help="Target .env files")
    p.add_argument("--ignore-values", action="store_true", help="Only check key presence")
    p.add_argument("--ignore-extra", action="store_true", help="Ignore extra keys in targets")
    p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    p.add_argument("--no-color", action="store_true")
    return p


def _run_compare(args: argparse.Namespace) -> int:
    if not args.baseline.exists():
        print(f"error: baseline file not found: {args.baseline}", file=sys.stderr)
        return 2
    missing = [t for t in args.targets if not t.exists()]
    if missing:
        for m in missing:
            print(f"error: target file not found: {m}", file=sys.stderr)
        return 2

    results = compare_many(
        args.baseline,
        args.targets,
        ignore_values=args.ignore_values,
        ignore_extra=args.ignore_extra,
    )

    if args.fmt == "json":
        print(report_comparison_json(results))
    else:
        print(report_comparison_text(results, use_color=not args.no_color))

    return 1 if any(r.has_differences() for r in results) else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="envguard-compare")
    sub = parser.add_subparsers(dest="cmd")
    build_compare_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_compare(args))
