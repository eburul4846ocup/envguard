"""CLI sub-command: scan — detect hardcoded secrets in a .env file."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.scanner import scan_env


def build_scan_parser(subparsers=None):
    description = "Scan a .env file for hardcoded secrets."
    if subparsers is not None:
        p = subparsers.add_parser("scan", help=description)
    else:
        p = argparse.ArgumentParser(prog="envguard scan", description=description)
    p.add_argument("file", help="Path to the .env file to scan")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_run_scan)
    return p


def _run_scan(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = scan_env(env)

    if args.fmt == "json":
        data = {
            "clean": result.is_clean,
            "hit_count": result.hit_count,
            "hits": [
                {"key": h.key, "pattern": h.pattern_name}
                for h in result.hits
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())

    return 0 if result.is_clean else 1


def main():
    parser = build_scan_parser()
    args = parser.parse_args()
    sys.exit(_run_scan(args))


if __name__ == "__main__":
    main()
