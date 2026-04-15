"""Integration tests for the `envguard merge` CLI sub-command."""
import json
from pathlib import Path

import pytest

from envguard.cli_merge import build_merge_parser, _run_merge
import argparse


@pytest.fixture()
def env_dir(tmp_path: Path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _make_args(files, strategy="last-wins", fmt="dotenv", output=None, show_conflicts=False):
    ns = argparse.Namespace(
        files=files,
        strategy=strategy,
        fmt=fmt,
        output=output,
        show_conflicts=show_conflicts,
        func=_run_merge,
    )
    return ns


def test_merge_no_conflict_exits_zero(env_dir):
    a = _write(env_dir / "a.env", "FOO=1\nBAR=2\n")
    b = _write(env_dir / "b.env", "BAZ=3\n")
    code = _run_merge(_make_args([str(a), str(b)]))
    assert code == 0


def test_merge_conflict_last_wins_exits_one(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=old\n")
    b = _write(env_dir / "b.env", "KEY=new\n")
    code = _run_merge(_make_args([str(a), str(b)], strategy="last-wins"))
    assert code == 1
    captured = capsys.readouterr()
    assert "KEY=new" in captured.out


def test_merge_conflict_first_wins(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=original\n")
    b = _write(env_dir / "b.env", "KEY=override\n")
    _run_merge(_make_args([str(a), str(b)], strategy="first-wins"))
    captured = capsys.readouterr()
    assert "KEY=original" in captured.out


def test_merge_strict_conflict_exits_one(env_dir, capsys):
    a = _write(env_dir / "a.env", "SECRET=aaa\n")
    b = _write(env_dir / "b.env", "SECRET=bbb\n")
    code = _run_merge(_make_args([str(a), str(b)], strategy="strict"))
    assert code == 1
    captured = capsys.readouterr()
    assert "SECRET" in captured.err


def test_merge_missing_file_exits_two(env_dir):
    code = _run_merge(_make_args([str(env_dir / "missing.env")]))
    assert code == 2


def test_merge_output_to_file(env_dir):
    a = _write(env_dir / "a.env", "FOO=1\n")
    out = env_dir / "merged.env"
    _run_merge(_make_args([str(a)], output=str(out)))
    assert out.exists()
    assert "FOO=1" in out.read_text()


def test_merge_show_conflicts_prints_to_stderr(env_dir, capsys):
    a = _write(env_dir / "a.env", "DB=old\n")
    b = _write(env_dir / "b.env", "DB=new\n")
    _run_merge(_make_args([str(a), str(b)], show_conflicts=True))
    captured = capsys.readouterr()
    assert "CONFLICT" in captured.err


def test_build_merge_parser_registers_subcommand():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_merge_parser(sub)
    args = root.parse_args(["merge", "a.env", "b.env", "--strategy", "first-wins"])
    assert args.strategy == "first-wins"
    assert args.files == ["a.env", "b.env"]
