"""Integration tests: parse a real .env file then filter it."""
from pathlib import Path

import pytest

from envguard.filterer import filter_env
from envguard.parser import parse_env_file


@pytest.fixture()
def tmp_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    return p


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_parse_then_filter_by_prefix(tmp_env):
    _write(
        tmp_env,
        'AWS_KEY="AKIA123"\nAWS_SECRET="s3cr3t"\nDB_HOST=localhost\nPORT=8080\n',
    )
    env = parse_env_file(tmp_env)
    result = filter_env(env, prefixes=["AWS_"])
    assert set(result.matched.keys()) == {"AWS_KEY", "AWS_SECRET"}
    assert result.match_count == 2


def test_parse_then_filter_by_pattern(tmp_env):
    _write(
        tmp_env,
        "DATABASE_URL=postgres://localhost/db\nREDIS_URL=redis://localhost\nSECRET=abc\n",
    )
    env = parse_env_file(tmp_env)
    result = filter_env(env, patterns=[r"_URL$"])
    assert "DATABASE_URL" in result.matched
    assert "REDIS_URL" in result.matched
    assert "SECRET" in result.excluded


def test_filter_then_export_subset(tmp_env):
    """Filtered matched dict can be used directly as a plain dict."""
    _write(tmp_env, "A=1\nB=2\nC=3\n")
    env = parse_env_file(tmp_env)
    result = filter_env(env, prefixes=["A", "B"])
    subset = result.matched
    assert subset == {"A": "1", "B": "2"}


def test_empty_file_filter_is_empty(tmp_env):
    _write(tmp_env, "")
    env = parse_env_file(tmp_env)
    result = filter_env(env, prefixes=["AWS_"])
    assert result.is_empty
    assert result.excluded_count == 0
