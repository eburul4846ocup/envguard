"""envguard CLI sub-command: stringify."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.stringer import stringify_env


def build_stringify_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "stringify",
        help="Render a .env file as formatted text.",
    )
    p.add_argument("file", help="Path to the .env file.")
    p.add_argument(
        "--quote-values",
        action="store_true",
        default=False,
        help="Always wrap values in double quotes.",
    )
    p.add_argument(
        "--no-sort",
        action="store_true",
        default=False,
        help="Preserve key order instead of sorting alphabetically.",
    )
    p.add_argument(
        "--separator",
        default="=",
        help="Separator between key and value (default: '=').",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        default="dotenv",
        help="Format label to embed in the summary (default: dotenv).",
    )
    return p


def _run_stringify(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = stringify_env(
        env,
        quote_values=args.quote_values,
        sort_keys=not args.no_sort,
        separator=args.separator,
        fmt=args.fmt,
    )

    print(result.to_string())
    print(f"# {result.summary()}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="envguard-stringify")
    sub = parser.add_subparsers(dest="command")
    build_stringify_parser(sub)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    sys.exit(_run_stringify(args))


if __name__ == "__main__":  # pragma: no cover
    main()
