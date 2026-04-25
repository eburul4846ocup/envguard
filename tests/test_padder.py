"""Tests for envguard.padder."""
from __future__ import annotations

import pytest

from envguard.padder import PadResult, pad_env


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# pad_env behaviour
# ---------------------------------------------------------------------------

class TestPadEnv:
    def test_empty_env_returns_empty_result(self):
        result = pad_env({})
        assert result.padded == {}
        assert result.width == 0
        assert not result.is_changed

    def test_single_key_width_equals_key_length(self):
        result = pad_env({"KEY": "value"})
        assert result.width == 3

    def test_width_is_longest_key(self):
        env = {"A": "1", "LONG_KEY": "2", "MID": "3"}
        result = pad_env(env)
        assert result.width == len("LONG_KEY")

    def test_min_width_overrides_when_larger(self):
        env = {"A": "1"}
        result = pad_env(env, min_width=10)
        assert result.width == 10

    def test_min_width_ignored_when_smaller(self):
        env = {"LONG_KEY": "v"}
        result = pad_env(env, min_width=2)
        assert result.width == len("LONG_KEY")

    def test_values_are_preserved_unchanged(self):
        env = {"A": "hello", "BB": "world"}
        result = pad_env(env)
        assert result.padded["A"] == "hello"
        assert result.padded["BB"] == "world"

    def test_keys_are_preserved(self):
        env = {"FOO": "1", "BAR": "2"}
        result = pad_env(env)
        assert set(result.padded.keys()) == {"FOO", "BAR"}


# ---------------------------------------------------------------------------
# PadResult helpers
# ---------------------------------------------------------------------------

class TestPadResult:
    def test_is_changed_false_when_all_same_length(self):
        env = {"KEY": "v"}
        result = pad_env(env)
        # Only one key; width == len("KEY") == 3, formatted == "KEY=v" unchanged
        assert not result.is_changed

    def test_is_changed_true_when_keys_differ_in_length(self):
        env = {"A": "1", "LONG_KEY": "2"}
        result = pad_env(env)
        # "A" will be padded to 8 chars, so at least one line changes
        assert result.is_changed

    def test_change_count_correct(self):
        env = {"A": "1", "BB": "2", "CCC": "3"}
        result = pad_env(env)
        # width == 3; only "CCC" is already at max width
        assert result.change_count == 2

    def test_to_string_aligns_equals_signs(self):
        env = {"A": "1", "LONG": "2"}
        result = pad_env(env)
        lines = result.to_string().splitlines()
        eq_positions = [line.index("=") for line in lines]
        assert len(set(eq_positions)) == 1, "All '=' should be at the same column"

    def test_to_string_ends_with_newline(self):
        result = pad_env({"K": "v"})
        assert result.to_string().endswith("\n")

    def test_summary_no_changes(self):
        result = pad_env({"KEY": "v"})
        assert "no changes" in result.summary()

    def test_summary_with_changes(self):
        result = pad_env({"A": "1", "LONG_KEY": "2"})
        assert "aligned" in result.summary()
        assert str(result.width) in result.summary()
