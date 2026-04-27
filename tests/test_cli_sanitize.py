"""Tests for the sanitize CLI subcommand."""
import argparse
from pathlib import Path
import pytest

from envguard.cli_sanitize import _run_sanitize


@pytest.fixture()
def env_file(tmp_path: Path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _args(file: str, **kwargs) -> argparse.Namespace:
    defaults = {
        "strip_null": True,
        "strip_ctrl": True,
        "collapse_spaces": False,
        "in_place": False,
        "quiet": True,
    }
    defaults.update(kwargs)
    return argparse.Namespace(file=file, **defaults)


def test_sanitize_clean_file_exits_zero(env_file: Path):
    _write(env_file, "FOO=bar\nBAZ=hello\n")
    code = _run_sanitize(_args(str(env_file)))
    assert code == 0


def test_sanitize_missing_file_exits_two(tmp_path: Path):
    code = _run_sanitize(_args(str(tmp_path / "missing.env")))
    assert code == 2


def test_sanitize_dirty_value_exits_one(env_file: Path):
    _write(env_file, "KEY=bad\x00val\n")
    code = _run_sanitize(_args(str(env_file)))
    assert code == 1


def test_sanitize_in_place_writes_file(env_file: Path):
    _write(env_file, "KEY=bad\x00val\n")
    code = _run_sanitize(_args(str(env_file), in_place=True))
    assert code == 1
    content = env_file.read_text(encoding="utf-8")
    assert "\x00" not in content
    assert "KEY=badval" in content


def test_sanitize_collapse_spaces_enabled(env_file: Path):
    _write(env_file, "MSG=hello   world\n")
    code = _run_sanitize(_args(str(env_file), collapse_spaces=True))
    assert code == 1


def test_sanitize_no_strip_null_leaves_null(env_file: Path):
    _write(env_file, "KEY=ok\n")
    code = _run_sanitize(_args(str(env_file), strip_null=False))
    assert code == 0
