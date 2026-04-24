"""Tests for envguard.cli_diff_env CLI entry-point."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envguard.cli_diff_env import build_diff_env_parser, _run_diff_env


@pytest.fixture()
def env_dir(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return tmp_path, _write


def _args(files, fmt="text", color=False):
    parser = build_diff_env_parser()
    argv = list(files)
    if fmt != "text":
        argv += ["--format", fmt]
    if color:
        argv.append("--color")
    return parser.parse_args(argv)


def test_no_issues_exits_zero(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=same\n")
    p2 = write(".env.prod", "KEY=same\n")
    args = _args([f"dev={p1}", f"prod={p2}"])
    assert _run_diff_env(args) == 0


def test_issues_exits_one(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=dev\n")
    p2 = write(".env.prod", "KEY=prod\n")
    args = _args([f"dev={p1}", f"prod={p2}"])
    assert _run_diff_env(args) == 1


def test_json_output_is_valid(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=x\n")
    p2 = write(".env.prod", "KEY=y\n")
    args = _args([f"dev={p1}", f"prod={p2}"], fmt="json")
    _run_diff_env(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "has_issues" in data
    assert data["has_issues"] is True


def test_missing_file_exits_two(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=x\n")
    args = _args([f"dev={p1}", "prod=/nonexistent/.env.prod"])
    assert _run_diff_env(args) == 2


def test_bad_spec_exits_two(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=x\n")
    args = _args([f"dev={p1}", "no-equals-sign"])
    assert _run_diff_env(args) == 2


def test_only_one_file_exits_two(env_dir, capsys):
    tmp, write = env_dir
    p1 = write(".env.dev", "KEY=x\n")
    args = _args([f"dev={p1}"])
    assert _run_diff_env(args) == 2
