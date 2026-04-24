"""Integration tests: parse → prune → re-parse round-trip."""
import textwrap
from pathlib import Path

import pytest

from envguard.parser import parse_env_file
from envguard.pruner import prune_env


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def test_parse_then_prune_exact_key(tmp_env):
    _write(tmp_env, """
        DB_HOST=localhost
        DB_PASS=secret
        PORT=5432
    """)
    env = parse_env_file(tmp_env)
    result = prune_env(env, keys=["DB_PASS"])
    assert "DB_PASS" not in result.result
    assert result.result["DB_HOST"] == "localhost"
    assert result.result["PORT"] == "5432"


def test_parse_prune_write_reparse(tmp_env):
    _write(tmp_env, """
        AWS_ACCESS_KEY_ID=AKIA123
        AWS_SECRET_ACCESS_KEY=abc/def
        APP_ENV=production
    """)
    env = parse_env_file(tmp_env)
    result = prune_env(env, patterns=[r"AWS_.*"])
    tmp_env.write_text(result.to_string(), encoding="utf-8")
    reparsed = parse_env_file(tmp_env)
    assert list(reparsed.keys()) == ["APP_ENV"]
    assert reparsed["APP_ENV"] == "production"


def test_prune_all_keys_yields_empty_file(tmp_env):
    _write(tmp_env, "A=1\nB=2\n")
    env = parse_env_file(tmp_env)
    result = prune_env(env, keys=["A", "B"])
    assert result.result == {}
    assert result.to_string() == ""


def test_quoted_values_survive_prune_round_trip(tmp_env):
    _write(tmp_env, 'GREETING="hello world"\nTOKEN=abc123\n')
    env = parse_env_file(tmp_env)
    result = prune_env(env, keys=["TOKEN"])
    assert result.result["GREETING"] == "hello world"
