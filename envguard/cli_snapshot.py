"""CLI sub-commands: snapshot capture / diff."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.parser import parse_env_file
from envguard.snapshot import capture, load_snapshot, save_snapshot


def build_snapshot_parser(sub: argparse._SubParsersAction) -> None:  # noqa: SLF001
    sp = sub.add_parser("snapshot", help="Capture or diff .env snapshots")
    ssub = sp.add_subparsers(dest="snapshot_cmd", required=True)

    # --- capture ---
    cap = ssub.add_parser("capture", help="Save a snapshot of an .env file")
    cap.add_argument("env_file", help="Path to .env file")
    cap.add_argument("output", help="Destination JSON snapshot file")
    cap.add_argument("--label", default=None, help="Optional human-readable label")

    # --- diff ---
    dif = ssub.add_parser("diff", help="Compare two snapshots")
    dif.add_argument("previous", help="Older snapshot JSON")
    dif.add_argument("current", help="Newer snapshot JSON")
    dif.add_argument("--no-values", action="store_true",
                     help="Hide values in diff output")


def _run_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_cmd == "capture":
        env = parse_env_file(Path(args.env_file))
        snap = capture(env, source=args.env_file, label=args.label)
        save_snapshot(snap, Path(args.output))
        print(f"Snapshot saved → {args.output} ({len(env)} keys)")
        return 0

    if args.snapshot_cmd == "diff":
        prev = load_snapshot(Path(args.previous))
        curr = load_snapshot(Path(args.current))

        added = curr.keys_added_since(prev)
        removed = curr.keys_removed_since(prev)
        changed = curr.keys_changed_since(prev)

        if not curr.has_changes_since(prev):
            print("No changes between snapshots.")
            return 0

        if added:
            for k in added:
                v = "" if args.no_values else f" = {curr.env[k]}"
                print(f"  + {k}{v}")
        if removed:
            for k in removed:
                v = "" if args.no_values else f" = {prev.env[k]}"
                print(f"  - {k}{v}")
        if changed:
            for k in changed:
                if args.no_values:
                    print(f"  ~ {k}")
                else:
                    print(f"  ~ {k}  {prev.env[k]!r} → {curr.env[k]!r}")
        return 1

    return 0  # unreachable
