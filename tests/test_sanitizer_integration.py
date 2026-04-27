"""Integration tests: parse → sanitize → re-parse pipeline."""
from pathlib import Path
import pytest

from envguard.parser import parse_env_file
from envguard.sanitizer import sanitize_env


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_bytes(content.encode("utf-8"))
    return path


def test_parse_then_sanitize_clean_env(tmp_env: Path):
    _write(tmp_env, "HOST=localhost\nPORT=5432\n")
    env = parse_env_file(tmp_env)
    result = sanitize_env(env)
    assert not result.is_changed
    assert result.sanitized == env


def test_parse_then_sanitize_removes_null(tmp_env: Path):
    _write(tmp_env, b"SECRET=abc\x00def\n")
    env = parse_env_file(tmp_env)
    result = sanitize_env(env)
    assert result.sanitized["SECRET"] == "abcdef"
    assert result.is_changed


def test_sanitize_write_reparse(tmp_env: Path):
    _write(tmp_env, b"KEY=val\x01ue\nOTHER=clean\n")
    env = parse_env_file(tmp_env)
    result = sanitize_env(env, strip_ctrl=True)
    tmp_env.write_text(result.to_string() + "\n", encoding="utf-8")
    reparsed = parse_env_file(tmp_env)
    assert "\x01" not in reparsed["KEY"]
    assert reparsed["OTHER"] == "clean"


def test_collapse_spaces_integration(tmp_env: Path):
    _write(tmp_env, "DESC=hello   world\nNAME=John  Doe\n")
    env = parse_env_file(tmp_env)
    result = sanitize_env(env, collapse_spaces=True)
    assert result.sanitized["DESC"] == "hello world"
    assert result.sanitized["NAME"] == "John Doe"
    assert result.change_count == 2
