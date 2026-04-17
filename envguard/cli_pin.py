"""CLI commands: envguard pin capture / envguard pin check."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.pinner import pin_env, save_pin, load_pin, detect_drift


def build_pin_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("pin", help="Pin and drift-check env variables")
    cmds = p.add_subparsers(dest="pin_cmd", required=True)

    cap = cmds.add_parser("capture", help="Save current env values to a lockfile")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("--lock", default=".env.lock", help="Lockfile path (default: .env.lock)")

    chk = cmds.add_parser("check", help="Detect drift against a lockfile")
    chk.add_argument("env_file", help="Path to .env file")
    chk.add_argument("--lock", default=".env.lock", help="Lockfile path (default: .env.lock)")


def _run_pin(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 2

    env = parse_env_file(env_path)

    if args.pin_cmd == "capture":
        lock = Path(args.lock)
        result = pin_env(env, source=str(env_path))
        save_pin(result, lock)
        print(result.summary())
        print(f"Lockfile written to '{lock}'")
        return 0

    if args.pin_cmd == "check":
        lock = Path(args.lock)
        if not lock.exists():
            print(f"error: lockfile not found: {lock}", file=sys.stderr)
            return 2
        pin = load_pin(lock)
        drift = detect_drift(pin, env)
        if not drift.has_drift():
            print("No drift detected.")
            return 0
        print(f"Drift detected: {drift.summary()}")
        for key, (old, new) in drift.drifted.items():
            print(f"  ~ {key}: '{old}' -> '{new}'")
        for key in drift.added:
            print(f"  + {key}")
        for key in drift.removed:
            print(f"  - {key}")
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="envguard-pin")
    sub = parser.add_subparsers(dest="pin_cmd", required=True)
    build_pin_parser(sub)
    args = parser.parse_args()
    sys.exit(_run_pin(args))
