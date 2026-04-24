"""Tests for envguard.pruner."""
import pytest
from envguard.pruner import prune_env, PruneResult


def _env(**kwargs) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# prune_count / is_changed
# ---------------------------------------------------------------------------

def test_no_keys_no_patterns_returns_unchanged():
    env = _env(A="1", B="2")
    r = prune_env(env)
    assert r.result == env
    assert r.prune_count == 0
    assert not r.is_changed


def test_exact_key_is_removed():
    env = _env(A="1", B="2", C="3")
    r = prune_env(env, keys=["B"])
    assert "B" not in r.result
    assert r.pruned == {"B": "2"}
    assert r.prune_count == 1
    assert r.is_changed


def test_multiple_exact_keys_removed():
    env = _env(A="1", B="2", C="3")
    r = prune_env(env, keys=["A", "C"])
    assert r.result == {"B": "2"}
    assert r.prune_count == 2


def test_missing_key_in_exact_list_is_ignored():
    env = _env(A="1")
    r = prune_env(env, keys=["NONEXISTENT"])
    assert r.result == {"A": "1"}
    assert r.prune_count == 0


# ---------------------------------------------------------------------------
# pattern matching
# ---------------------------------------------------------------------------

def test_pattern_removes_matching_keys():
    env = _env(AWS_ACCESS_KEY="x", AWS_SECRET="y", PORT="8080")
    r = prune_env(env, patterns=[r"AWS_.*"])
    assert "PORT" in r.result
    assert "AWS_ACCESS_KEY" not in r.result
    assert "AWS_SECRET" not in r.result
    assert r.prune_count == 2


def test_pattern_fullmatch_does_not_remove_partial():
    env = _env(MY_TOKEN="t", TOKEN_OLD="o")
    # pattern anchored to full key — TOKEN alone should not match MY_TOKEN
    r = prune_env(env, patterns=[r"TOKEN"])
    assert r.result == {"MY_TOKEN": "t", "TOKEN_OLD": "o"}
    assert r.prune_count == 0


def test_pattern_and_exact_combined():
    env = _env(A="1", B_X="2", B_Y="3", C="4")
    r = prune_env(env, keys=["A"], patterns=[r"B_.*"])
    assert r.result == {"C": "4"}
    assert r.prune_count == 3


# ---------------------------------------------------------------------------
# summary / to_string
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    r = prune_env(_env(A="1"))
    assert r.summary() == "No keys pruned."


def test_summary_with_changes():
    r = prune_env(_env(A="1", B="2"), keys=["A", "B"])
    assert "2" in r.summary()
    assert "key(s)" in r.summary()


def test_to_string_sorted_output():
    env = _env(Z="last", A="first", M="mid")
    r = prune_env(env, keys=["M"])
    lines = r.to_string().strip().splitlines()
    assert lines == ["A=first", "Z=last"]


def test_to_string_empty_result():
    r = prune_env(_env(A="1"), keys=["A"])
    assert r.to_string() == ""


def test_original_is_not_mutated():
    env = _env(A="1", B="2")
    original_copy = dict(env)
    prune_env(env, keys=["A"])
    assert env == original_copy
