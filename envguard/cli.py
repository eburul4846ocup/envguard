"""CLI entry point for envguard."""

import argparse
import json
import sys
from typing import List, Optional

from envguard.parser import parse_env_file
from envguard.comparator import compare_envs
from envguard.reporter import report_text, report_json, OutputFormat
from envguard.validator import validate_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Validate and diff .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- diff command ---
    diff_cmd = subparsers.add_parser("diff", help="Compare two .env files.")
    diff_cmd.add_argument("source", help="Source .env file (reference).")
    diff_cmd.add_argument("target", help="Target .env file to compare against.")
    diff_cmd.add_argument(
        "--ignore-values",
        action="store_true",
        help="Only check for missing/extra keys, not value differences.",
    )
    diff_cmd.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    diff_cmd.add_argument(
        "--no-color", action="store_true", help="Disable colored output."
    )

    # --- validate command ---
    val_cmd = subparsers.add_parser("validate", help="Validate a .env file.")
    val_cmd.add_argument("envfile", help="The .env file to validate.")
    val_cmd.add_argument(
        "--require",
        nargs="+",
        metavar="KEY",
        help="Keys that must be present.",
    )
    val_cmd.add_argument(
        "--pattern",
        nargs="+",
        metavar="KEY=TYPE",
        help="Value format checks, e.g. DATABASE_URL=url PORT=port.",
    )
    val_cmd.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow keys with empty values without warning.",
    )
    val_cmd.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
    )

    return parser


def _parse_key_patterns(pattern_args: Optional[List[str]]) -> dict:
    patterns = {}
    if not pattern_args:
        return patterns
    for item in pattern_args:
        if "=" not in item:
            print(f"Warning: ignoring malformed --pattern argument: {item!r}", file=sys.stderr)
            continue
        key, _, ptype = item.partition("=")
        patterns[key.strip()] = ptype.strip()
    return patterns


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        source_env = parse_env_file(args.source)
        target_env = parse_env_file(args.target)
        result = compare_envs(source_env, target_env, ignore_values=args.ignore_values)
        fmt = OutputFormat.JSON if args.output_format == "json" else OutputFormat.TEXT
        if fmt == OutputFormat.JSON:
            print(report_json(result))
        else:
            print(report_text(result, use_color=not args.no_color))
        return 0 if not result.has_differences else 1

    if args.command == "validate":
        env = parse_env_file(args.envfile)
        key_patterns = _parse_key_patterns(getattr(args, "pattern", None))
        val_result = validate_env(
            env,
            required_keys=args.require,
            key_patterns=key_patterns or None,
            allow_empty_values=args.allow_empty,
        )
        if args.output_format == "json":
            data = {
                "valid": val_result.is_valid,
                "errors": [str(i) for i in val_result.errors],
                "warnings": [str(i) for i in val_result.warnings],
            }
            print(json.dumps(data, indent=2))
        else:
            if not val_result.issues:
                print("✔ No issues found.")
            for issue in val_result.issues:
                print(str(issue))
        return 0 if val_result.is_valid else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
