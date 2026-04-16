"""Tests for envguard.stripper."""
import pytest
from pathlib import Path
from envguard.stripper import strip_env


@pytest.fixture
def env_file(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_no_comments_or_blanks_unchanged(env_file):
    p = env_file("FOO=bar\nBAZ=qux\n")
    result = strip_env(p)
    assert not result.is_changed
    assert result.removed_comments == 0
    assert result.removed_blanks == 0


def test_removes_comment_lines(env_file):
    p = env_file("# comment\nFOO=bar\n")
    result = strip_env(p)
    assert result.removed_comments == 1
    assert "FOO=bar" in result.lines
    assert not any(l.startswith("#") for l in result.lines)


def test_removes_blank_lines(env_file):
    p = env_file("FOO=bar\n\nBAZ=qux\n")
    result = strip_env(p)
    assert result.removed_blanks == 1
    assert result.stripped_lines == 2


def test_keep_comments_flag(env_file):
    p = env_file("# keep me\nFOO=bar\n")
    result = strip_env(p, keep_comments=True)
    assert result.removed_comments == 0
    assert any(l.startswith("#") for l in result.lines)


def test_keep_blanks_flag(env_file):
    p = env_file("FOO=bar\n\nBAZ=qux\n")
    result = strip_env(p, keep_blanks=True)
    assert result.removed_blanks == 0
    assert result.stripped_lines == 3


def test_summary_no_change(env_file):
    p = env_file("FOO=bar\n")
    result = strip_env(p)
    assert result.summary() == "Nothing to strip."


def test_summary_with_changes(env_file):
    p = env_file("# comment\n\nFOO=bar\n")
    result = strip_env(p)
    assert "1 comment" in result.summary()
    assert "1 blank" in result.summary()


def test_to_string_ends_with_newline(env_file):
    p = env_file("# comment\nFOO=bar\n")
    result = strip_env(p)
    assert result.to_string().endswith("\n")


def test_empty_file(env_file):
    p = env_file("")
    result = strip_env(p)
    assert result.stripped_lines == 0
    assert result.to_string() == ""
