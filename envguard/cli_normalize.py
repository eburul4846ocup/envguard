"""CLI sub-command: normalize — clean up .env values in place or preview."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.normalizer import normalize_env


def build_normalize_parser(sub=None):
    kwargs = dict(description="Normalize .env values (strip quotes, unify booleans).")
    if sub is not None:
        p = sub.add_parser("normalize", **kwargs)
    else:
        p = argparse.ArgumentParser(**kwargs)
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--no-strip-quotes", action="store_true", help="Keep surrounding quotes")
    p.add_argument("--no-lowercase-booleans", action="store_true", help="Keep boolean case")
    p.add_argument("--in-place", action="store_true", help="Write changes back to file")
    p.add_argument("--quiet", action="store_true", help="Suppress output")
    return p


def _run_normalize(args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env = parse_env_file(path)
    result = normalize_env(
        env,
        strip_quotes=not args.no_strip_quotes,
        lowercase_booleans=not args.no_lowercase_booleans,
    )

    if not args.quiet:
        print(result.summary())

    if args.in_place and result.is_changed:
        path.write_text(result.to_string())
        if not args.quiet:
            print(f"Written to {path}")

    return 1 if result.is_changed else 0


def main():
    parser = build_normalize_parser()
    sys.exit(_run_normalize(parser.parse_args()))


if __name__ == "__main__":
    main()
