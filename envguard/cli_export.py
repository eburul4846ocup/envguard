"""CLI sub-command: envguard export — dump a .env file in another format."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.exporter import ExportFormat, export_env
from envguard.parser import parse_env_file


def build_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *export* sub-command onto *subparsers*."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "export",
        help="Export a .env file in shell, json, or dotenv format.",
    )
    p.add_argument("env_file", metavar="ENV_FILE", help="Path to the .env file.")
    p.add_argument(
        "--format",
        "-f",
        dest="fmt",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.DOTENV.value,
        help="Output format (default: dotenv).",
    )
    p.add_argument(
        "--output",
        "-o",
        dest="output",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    p.set_defaults(func=_run_export)


def _run_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command; returns an exit code."""
    path = Path(args.env_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    env = parse_env_file(path)
    fmt = ExportFormat(args.fmt)
    result = export_env(env, fmt=fmt)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(result, encoding="utf-8")
        print(f"Exported {len(env)} variable(s) to {out_path}")
    else:
        sys.stdout.write(result)

    return 0
