"""Integration tests: strip then parse."""
from pathlib import Path
import pytest

from envguard.stripper import strip_env
from envguard.parser import parse_env_file


@pytest.fixture
def tmp_env(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_strip_then_parse_yields_correct_keys(tmp_env):
    p = tmp_env("# database config\nDB_HOST=localhost\n\nDB_PORT=5432\n")
    result = strip_env(p)
    stripped_path = p.with_suffix(".stripped.env")
    stripped_path.write_text(result.to_string(), encoding="utf-8")
    env = parse_env_file(stripped_path)
    assert env == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_strip_in_place_then_parse(tmp_env):
    p = tmp_env("# ignore\nFOO=1\n\nBAR=2\n")
    result = strip_env(p)
    p.write_text(result.to_string(), encoding="utf-8")
    env = parse_env_file(p)
    assert "FOO" in env
    assert "BAR" in env
    assert len(env) == 2


def test_strip_all_comments_empty_result(tmp_env):
    p = tmp_env("# only comments\n# nothing else\n")
    result = strip_env(p)
    assert result.stripped_lines == 0
    assert result.to_string() == ""


def test_no_data_lost_when_keep_all(tmp_env):
    content = "# comment\nFOO=bar\n\nBAZ=qux\n"
    p = tmp_env(content)
    result = strip_env(p, keep_comments=True, keep_blanks=True)
    assert result.original_lines == result.stripped_lines
    assert not result.is_changed
