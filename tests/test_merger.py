"""Tests for envguard.merger."""
import pytest

from envguard.merger import (
    MergeConflict,
    MergeError,
    MergeResult,
    MergeStrategy,
    merge_envs,
)


def _src(path: str, **kwargs: str):
    return (path, dict(kwargs))


# ---------------------------------------------------------------------------
# No conflicts
# ---------------------------------------------------------------------------

def test_no_conflicts_merges_all_keys():
    result = merge_envs([
        _src("a.env", FOO="1", BAR="2"),
        _src("b.env", BAZ="3"),
    ])
    assert result.merged == {"FOO": "1", "BAR": "2", "BAZ": "3"}
    assert not result.has_conflicts


def test_empty_sources_returns_empty():
    result = merge_envs([])
    assert result.merged == {}
    assert not result.has_conflicts


def test_single_source_passthrough():
    result = merge_envs([_src("only.env", KEY="value")])
    assert result.merged == {"KEY": "value"}


# ---------------------------------------------------------------------------
# LAST_WINS (default)
# ---------------------------------------------------------------------------

def test_last_wins_override():
    result = merge_envs([
        _src("base.env", DB_URL="postgres://old"),
        _src("override.env", DB_URL="postgres://new"),
    ], strategy=MergeStrategy.LAST_WINS)
    assert result.merged["DB_URL"] == "postgres://new"
    assert result.has_conflicts
    assert result.conflicts[0].key == "DB_URL"


def test_last_wins_conflict_records_both_values():
    result = merge_envs([
        _src("a.env", X="1"),
        _src("b.env", X="2"),
    ])
    conflict = result.conflicts[0]
    paths = [p for p, _ in conflict.values]
    assert "a.env" in paths
    assert "b.env" in paths


# ---------------------------------------------------------------------------
# FIRST_WINS
# ---------------------------------------------------------------------------

def test_first_wins_keeps_original_value():
    result = merge_envs([
        _src("base.env", SECRET="original"),
        _src("local.env", SECRET="override"),
    ], strategy=MergeStrategy.FIRST_WINS)
    assert result.merged["SECRET"] == "original"
    assert result.has_conflicts


# ---------------------------------------------------------------------------
# STRICT
# ---------------------------------------------------------------------------

def test_strict_raises_on_conflict():
    with pytest.raises(MergeError, match="Conflict on key 'API_KEY'"):
        merge_envs([
            _src("a.env", API_KEY="aaa"),
            _src("b.env", API_KEY="bbb"),
        ], strategy=MergeStrategy.STRICT)


def test_strict_no_conflict_succeeds():
    result = merge_envs([
        _src("a.env", FOO="1"),
        _src("b.env", BAR="2"),
    ], strategy=MergeStrategy.STRICT)
    assert result.merged == {"FOO": "1", "BAR": "2"}


# ---------------------------------------------------------------------------
# MergeConflict __str__
# ---------------------------------------------------------------------------

def test_conflict_str_representation():
    c = MergeConflict(key="PORT", values=[("a.env", "3000"), ("b.env", "4000")])
    text = str(c)
    assert "PORT" in text
    assert "3000" in text
    assert "4000" in text
