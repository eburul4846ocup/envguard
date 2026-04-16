"""Tests for envguard.cli_strip."""
import pytest
from pathlib import Path
from types import SimpleNamespace

from envguard.cli_strip import _run_strip


@pytest.fixture
def env_file(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def _args(file, *, keep_comments=False, keep_blanks=False, in_place=False, quiet=True):
    return SimpleNamespace(
        file=file,
        keep_comments=keep_comments,
        keep_blanks=keep_blanks,
        in_place=in_place,
        quiet=quiet,
    )


def test_strip_exits_zero_for_valid_file(env_file):
    p = env_file("FOO=bar\n")
    assert _run_strip(_args(p)) == 0


def test_strip_missing_file_exits_two(tmp_path):
    assert _run_strip(_args(tmp_path / "missing.env")) == 2


def test_strip_removes_comments(env_file, capsys):
    p = env_file("# comment\nFOO=bar\n")
    _run_strip(_args(p, quiet=True))
    captured = capsys.readouterr()
    assert "# comment" not in captured.out
    assert "FOO=bar" in captured.out


def test_strip_in_place_modifies_file(env_file):
    p = env_file("# comment\nFOO=bar\n")
    _run_strip(_args(p, in_place=True))
    content = p.read_text()
    assert "# comment" not in content
    assert "FOO=bar" in content


def test_strip_keep_comments_flag(env_file, capsys):
    p = env_file("# keep\nFOO=bar\n")
    _run_strip(_args(p, keep_comments=True, quiet=True))
    captured = capsys.readouterr()
    assert "# keep" in captured.out


def test_strip_keep_blanks_flag(env_file, capsys):
    p = env_file("FOO=bar\n\nBAZ=qux\n")
    _run_strip(_args(p, keep_blanks=True, quiet=True))
    captured = capsys.readouterr()
    assert captured.out.count("\n") >= 3


def test_strip_quiet_suppresses_summary(env_file, capsys):
    p = env_file("# c\nFOO=bar\n")
    _run_strip(_args(p, quiet=True))
    captured = capsys.readouterr()
    assert "Removed" not in captured.out
