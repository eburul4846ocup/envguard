"""CLI sub-command: envguard audit — scan a .env file for secret exposure risks."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envguard.auditor import AuditSeverity, audit_env
from envguard.parser import parse_env_file


def build_audit_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Scan a .env file for secret-like keys with real or missing values."
    if subparsers is not None:
        parser = subparsers.add_parser("audit", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envguard audit", description=description)

    parser.add_argument("file", help="Path to the .env file to audit")
    parser.add_argument(
        "--no-placeholders",
        dest="flag_placeholders",
        action="store_false",
        default=True,
        help="Do not warn about obvious placeholder values",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit 1 on warnings as well as errors",
    )
    parser.set_defaults(func=_run_audit)
    return parser


def _run_audit(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = audit_env(env, flag_placeholders=args.flag_placeholders)

    if args.format == "json":
        payload = [
            {"key": i.key, "severity": i.severity.value, "message": i.message}
            for i in result.issues
        ]
        print(json.dumps(payload, indent=2))
    else:
        if result.is_clean:
            print(f"OK  {path}  — no audit issues found.")
        else:
            for issue in result.issues:
                print(str(issue))

    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    _parser = build_audit_parser()
    _args = _parser.parse_args()
    sys.exit(_run_audit(_args))
