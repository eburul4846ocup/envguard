"""Tests for envguard.parser."""

import textwrap
from pathlib import Path

import pytest

from envguard.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path):
    """Factory that writes content to a temp .env file and returns its path."""

    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    return _write


def test_basic_key_value(env_file):
    path = env_file("""
        APP_ENV=production
        PORT=8080
    """)
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production", "PORT": "8080"}


def test_double_quoted_value(env_file):
    path = env_file('SECRET="my secret value"\n')
    assert parse_env_file(path)["SECRET"] == "my secret value"


def test_single_quoted_value(env_file):
    path = env_file("TOKEN='abc123'\n")
    assert parse_env_file(path)["TOKEN"] == "abc123"


def test_empty_value(env_file):
    path = env_file("EMPTY=\n")
    assert parse_env_file(path)["EMPTY"] == ""


def test_comments_and_blanks_ignored(env_file):
    path = env_file("""
        # This is a comment
        KEY=value

        # Another comment
        OTHER=123
    """)
    result = parse_env_file(path)
    assert list(result.keys()) == ["KEY", "OTHER"]


def test_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / "missing.env")


def test_malformed_line_raises(env_file):
    path = env_file("THIS IS NOT VALID\n")
    with pytest.raises(ValueError, match="Malformed line"):
        parse_env_file(path)


def test_spaces_around_equals(env_file):
    path = env_file("  DB_HOST  =  localhost  \n")
    assert parse_env_file(path)["DB_HOST"] == "localhost"
