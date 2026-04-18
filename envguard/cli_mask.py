"""CLI entry-point for the mask command."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.masker import mask_env


def build_mask_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    kwargs = dict(description="Mask sensitive values in a .env file for safe display.")
    parser = sub.add_parser("mask", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument("--visible-chars", type=int, default=0, metavar="N",
                        help="Leave last N characters of each masked value visible")
    parser.add_argument("--mask-char", default="*", metavar="CHAR",
                        help="Character used for masking (default: *)")
    parser.add_argument("--custom-keys", nargs="*", default=[], metavar="KEY",
                        help="Additional key names to treat as sensitive")
    parser.add_argument("--json", dest="json_output", action="store_true",
                        help="Output masked env as JSON")
    return parser


def _run_mask(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = mask_env(
        env,
        mask_char=args.mask_char,
        visible_chars=args.visible_chars,
        custom_keys=set(args.custom_keys) if args.custom_keys else None,
    )

    if args.json_output:
        print(json.dumps(result.masked, indent=2))
    else:
        print(result.summary())
        for key, value in result.masked.items():
            print(f"{key}={value}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_mask_parser()
    args = parser.parse_args()
    sys.exit(_run_mask(args))


if __name__ == "__main__":  # pragma: no cover
    main()
