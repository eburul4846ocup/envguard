"""Tests for envguard.deduplicator."""
from __future__ import annotations

from pathlib import Path

import pytest

from envguard.deduplicator import DeduplicateResult, deduplicate_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# DeduplicateResult unit tests
# ---------------------------------------------------------------------------

def test_is_clean_when_no_duplicates():
    result = DeduplicateResult(env={"A": "1"}, removed={})
    assert result.is_clean


def test_is_not_clean_when_duplicates_present():
    result = DeduplicateResult(env={"A": "2"}, removed={"A": ["1"]})
    assert not result.is_clean


def test_duplicate_count_sums_all_removed_values():
    result = DeduplicateResult(
        env={"A": "3", "B": "y"},
        removed={"A": ["1", "2"], "B": ["x"]},
    )
    assert result.duplicate_count == 3


def test_summary_clean():
    result = DeduplicateResult(env={}, removed={})
    assert "No duplicate" in result.summary()


def test_summary_with_duplicates():
    result = DeduplicateResult(env={"FOO": "b"}, removed={"FOO": ["a"]})
    summary = result.summary()
    assert "1" in summary
    assert "FOO" in summary


# ---------------------------------------------------------------------------
# deduplicate_env integration tests
# ---------------------------------------------------------------------------

def test_no_duplicates_is_clean(env_file: Path):
    _write(env_file, "A=1\nB=2\nC=3\n")
    result = deduplicate_env(env_file)
    assert result.is_clean
    assert result.env == {"A": "1", "B": "2", "C": "3"}


def test_single_duplicate_keeps_last_value(env_file: Path):
    _write(env_file, "FOO=first\nBAR=hello\nFOO=second\n")
    result = deduplicate_env(env_file)
    assert result.env["FOO"] == "second"
    assert result.removed["FOO"] == ["first"]


def test_multiple_duplicates_of_same_key(env_file: Path):
    _write(env_file, "X=1\nX=2\nX=3\n")
    result = deduplicate_env(env_file)
    assert result.env["X"] == "3"
    assert result.duplicate_count == 2


def test_comments_and_blanks_ignored(env_file: Path):
    content = "# comment\n\nA=1\n\n# another\nA=2\n"
    _write(env_file, content)
    result = deduplicate_env(env_file)
    assert result.env["A"] == "2"
    assert result.duplicate_count == 1


def test_quoted_values_stripped_before_dedup(env_file: Path):
    _write(env_file, 'KEY="alpha"\nKEY=beta\n')
    result = deduplicate_env(env_file)
    assert result.env["KEY"] == "beta"
    assert result.removed["KEY"] == ["alpha"]


def test_multiple_keys_with_duplicates(env_file: Path):
    _write(env_file, "A=1\nB=x\nA=2\nB=y\nC=only\n")
    result = deduplicate_env(env_file)
    assert result.env == {"A": "2", "B": "y", "C": "only"}
    assert set(result.removed.keys()) == {"A", "B"}
    assert result.duplicate_count == 2
