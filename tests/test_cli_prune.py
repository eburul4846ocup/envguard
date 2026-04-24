"""CLI tests for envguard.cli_prune."""
import textwrap
from pathlib import Path

import pytest

from envguard.cli_prune import build_prune_parser, _run_prune


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _args(file: str, keys=(), patterns=(), in_place=False, quiet=False):
    import argparse
    ns = argparse.Namespace(
        file=file,
        keys=list(keys),
        patterns=list(patterns),
        in_place=in_place,
        quiet=quiet,
    )
    return ns


def test_prune_no_changes_exits_zero(env_file):
    _write(env_file, "A=1\nB=2\n")
    code = _run_prune(_args(str(env_file)))
    assert code == 0


def test_prune_removes_key_exits_one(env_file):
    _write(env_file, "A=1\nB=2\n")
    code = _run_prune(_args(str(env_file), keys=["A"]))
    assert code == 1


def test_prune_missing_file_exits_two(env_file):
    code = _run_prune(_args(str(env_file)))
    assert code == 2


def test_prune_in_place_writes_file(env_file):
    _write(env_file, "SECRET=abc\nPORT=8080\n")
    _run_prune(_args(str(env_file), keys=["SECRET"], in_place=True))
    content = env_file.read_text()
    assert "SECRET" not in content
    assert "PORT=8080" in content


def test_prune_pattern_removes_matching(env_file):
    _write(env_file, "AWS_KEY=x\nAWS_SECRET=y\nPORT=9000\n")
    code = _run_prune(_args(str(env_file), patterns=[r"AWS_.*"], in_place=True))
    assert code == 1
    content = env_file.read_text()
    assert "AWS_KEY" not in content
    assert "PORT=9000" in content


def test_prune_stdout_output(env_file, capsys):
    _write(env_file, "A=1\nB=2\n")
    _run_prune(_args(str(env_file), keys=["B"]))
    out = capsys.readouterr().out
    assert "A=1" in out
    assert "B" not in out


def test_prune_quiet_suppresses_summary(env_file, capsys):
    _write(env_file, "A=1\n")
    _run_prune(_args(str(env_file), keys=["A"], quiet=True))
    out = capsys.readouterr().out
    # summary line should not appear; only the (empty) dotenv output
    assert "Pruned" not in out
