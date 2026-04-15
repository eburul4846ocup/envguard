"""Command-line interface for envguard.

Provides the main entry point and argument parsing for the envguard CLI tool.
Users can compare .env files across environments and output results in
different formats.
"""

import argparse
import sys
from pathlib import Path

from envguard.comparator import compare_envs
from envguard.parser import parse_env_file
from envguard.reporter import OutputFormat, report_json, report_text


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="envguard",
        description=(
            "Validate and diff .env files across environments to catch "
            "missing or mismatched variables before deployment."
        ),
    )

    parser.add_argument(
        "source",
        metavar="SOURCE",
        help="Path to the reference .env file (e.g. .env.example).",
    )
    parser.add_argument(
        "target",
        metavar="TARGET",
        help="Path to the target .env file to validate against the source.",
    )
    parser.add_argument(
        "--ignore-values",
        action="store_true",
        default=False,
        help=(
            "Only check for key presence; skip value mismatch reporting. "
            "Useful when comparing an example file that has placeholder values."
        ),
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="output_format",
        help="Output format for the comparison report (default: text).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color codes in text output.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run envguard and return an exit code.

    Returns:
        0 if no differences were found.
        1 if differences were detected or an error occurred.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    target_path = Path(args.target)

    # Validate that both files exist before attempting to parse them.
    for path in (source_path, target_path):
        if not path.exists():
            print(f"envguard: error: file not found: {path}", file=sys.stderr)
            return 1
        if not path.is_file():
            print(f"envguard: error: not a file: {path}", file=sys.stderr)
            return 1

    try:
        source_vars = parse_env_file(source_path)
        target_vars = parse_env_file(target_path)
    except OSError as exc:
        print(f"envguard: error: {exc}", file=sys.stderr)
        return 1

    result = compare_envs(
        source_vars,
        target_vars,
        ignore_values=args.ignore_values,
    )

    output_format = OutputFormat(args.output_format)

    if output_format == OutputFormat.JSON:
        print(report_json(result))
    else:
        use_color = not args.no_color
        print(report_text(result, color=use_color))

    # Exit with a non-zero status when differences are found so that CI
    # pipelines can treat a failed comparison as a build failure.
    return 1 if result.has_differences() else 0


if __name__ == "__main__":
    sys.exit(main())
