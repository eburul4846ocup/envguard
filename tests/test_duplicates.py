"""Tests for envguard.duplicates."""
from __future__ import annotations

from pathlib import Path

import pytest

from envguard.duplicates import find_duplicates


@pytest.fixture()
def env_file(tmp_path: Path):
    p = tmp_path / ".env"
    return p


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def test_no_duplicates_is_clean(env_file):
    _write(env_file, "FOO=bar\nBAZ=qux\n")
    result = find_duplicates(env_file)
    assert result.is_clean
    assert result.duplicate_count == 0


def test_single_duplicate_detected(env_file):
    _write(env_file, "FOO=first\nBAR=hello\nFOO=second\n")
    result = find_duplicates(env_file)
    assert not result.is_clean
    assert "FOO" in result.duplicates
    assert result.duplicates["FOO"] == [1, 3]


def test_multiple_duplicates_detected(env_file):
    _write(env_file, "A=1\nB=2\nA=3\nB=4\nC=5\n")
    result = find_duplicates(env_file)
    assert result.duplicate_count == 2
    assert set(result.duplicates.keys()) == {"A", "B"}


def test_comments_and_blank_lines_ignored(env_file):
    content = "# This is a comment\n\nFOO=bar\n# FOO=ignored\nFOO=baz\n"
    _write(env_file, content)
    result = find_duplicates(env_file)
    assert "FOO" in result.duplicates
    assert result.duplicates["FOO"] == [3, 5]


def test_three_occurrences_tracked(env_file):
    _write(env_file, "KEY=a\nKEY=b\nKEY=c\n")
    result = find_duplicates(env_file)
    assert result.duplicates["KEY"] == [1, 2, 3]


def test_summary_clean(env_file):
    _write(env_file, "X=1\n")
    result = find_duplicates(env_file)
    assert "no duplicate" in result.summary()


def test_summary_shows_duplicate_keys(env_file):
    _write(env_file, "ALPHA=1\nALPHA=2\n")
    result = find_duplicates(env_file)
    summary = result.summary()
    assert "ALPHA" in summary
    assert "1" in summary
    assert "2" in summary


def test_path_stored_on_result(env_file):
    _write(env_file, "FOO=bar\n")
    result = find_duplicates(env_file)
    assert result.path == env_file


def test_empty_file_is_clean(env_file):
    _write(env_file, "")
    result = find_duplicates(env_file)
    assert result.is_clean
