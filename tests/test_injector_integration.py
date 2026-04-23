"""Integration tests: parse a real .env file then inject it."""
from pathlib import Path

import pytest

from envguard.injector import inject_env
from envguard.parser import parse_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path):
    return tmp_path / ".env"


def _write(path: Path, text: str) -> Path:
    path.write_text(text)
    return path


def test_parse_then_inject_all_keys(tmp_env: Path):
    _write(tmp_env, 'DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY="abc123"\n')
    env = parse_env_file(str(tmp_env))
    result = inject_env(env, target={})
    assert result.inject_count == 3
    assert result.injected["DB_HOST"] == "localhost"
    assert result.injected["DB_PORT"] == "5432"
    assert result.injected["SECRET_KEY"] == "abc123"


def test_parse_then_inject_skips_existing(tmp_env: Path):
    _write(tmp_env, "FOO=new\nBAR=also_new\n")
    env = parse_env_file(str(tmp_env))
    result = inject_env(env, target={"FOO": "old"})
    assert "FOO" in result.skipped
    assert "BAR" in result.injected


def test_parse_then_inject_with_override(tmp_env: Path):
    _write(tmp_env, "FOO=new\n")
    env = parse_env_file(str(tmp_env))
    result = inject_env(env, target={"FOO": "old"}, override=True)
    assert result.overridden["FOO"] == "new"
    assert result.skip_count == 0


def test_merged_env_reflects_full_state(tmp_env: Path):
    _write(tmp_env, "A=1\nB=2\n")
    env = parse_env_file(str(tmp_env))
    base = {"C": "3", "A": "old"}
    result = inject_env(env, target=base, override=True)
    merged = result.merged_env(base=base)
    assert merged["A"] == "1"   # overridden
    assert merged["B"] == "2"   # injected
    assert merged["C"] == "3"   # untouched base key


def test_empty_env_file_produces_no_injections(tmp_env: Path):
    _write(tmp_env, "# just a comment\n")
    env = parse_env_file(str(tmp_env))
    result = inject_env(env, target={"EXISTING": "val"})
    assert result.inject_count == 0
    assert result.is_changed is False
