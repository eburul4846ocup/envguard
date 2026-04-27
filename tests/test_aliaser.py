"""Tests for envguard.aliaser."""
from __future__ import annotations

import pytest

from envguard.aliaser import alias_env, AliasResult


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

class TestAliasEnvBasic:
    def test_empty_env_returns_empty_result(self):
        result = alias_env({}, {})
        assert result.env == {}
        assert result.applied == []
        assert result.skipped == []

    def test_no_aliases_passthrough(self):
        env = _env(FOO="bar", BAZ="qux")
        result = alias_env(env, {})
        assert result.env == env
        assert result.change_count == 0
        assert not result.is_changed

    def test_single_alias_applied(self):
        env = _env(OLD_KEY="value")
        result = alias_env(env, {"NEW_KEY": "OLD_KEY"})
        assert "NEW_KEY" in result.env
        assert result.env["NEW_KEY"] == "value"
        assert "OLD_KEY" not in result.env  # removed by default

    def test_applied_list_contains_new_key(self):
        env = _env(SRC="hello")
        result = alias_env(env, {"DST": "SRC"})
        assert "DST" in result.applied

    def test_removed_list_contains_old_key(self):
        env = _env(SRC="hello")
        result = alias_env(env, {"DST": "SRC"})
        assert "SRC" in result.removed

    def test_missing_source_goes_to_skipped(self):
        env = _env(FOO="bar")
        result = alias_env(env, {"NEW": "MISSING"})
        assert "NEW" in result.skipped
        assert "NEW" not in result.env


# ---------------------------------------------------------------------------
# keep_original flag
# ---------------------------------------------------------------------------

class TestKeepOriginal:
    def test_keep_original_preserves_source_key(self):
        env = _env(API_KEY="secret")
        result = alias_env(env, {"TOKEN": "API_KEY"}, keep_original=True)
        assert "API_KEY" in result.env
        assert "TOKEN" in result.env

    def test_keep_original_removed_list_is_empty(self):
        env = _env(API_KEY="secret")
        result = alias_env(env, {"TOKEN": "API_KEY"}, keep_original=True)
        assert result.removed == []

    def test_keep_original_value_matches(self):
        env = _env(DB_PASS="hunter2")
        result = alias_env(env, {"DB_PASSWORD": "DB_PASS"}, keep_original=True)
        assert result.env["DB_PASSWORD"] == result.env["DB_PASS"] == "hunter2"


# ---------------------------------------------------------------------------
# Multiple aliases & summary
# ---------------------------------------------------------------------------

class TestMultipleAliases:
    def test_multiple_aliases_all_applied(self):
        env = _env(A="1", B="2", C="3")
        result = alias_env(env, {"X": "A", "Y": "B", "Z": "C"})
        assert set(result.applied) == {"X", "Y", "Z"}
        assert result.env == {"X": "1", "Y": "2", "Z": "3"}

    def test_summary_contains_applied_count(self):
        env = _env(OLD="v")
        result = alias_env(env, {"NEW": "OLD"})
        assert "1 alias(es) applied" in result.summary()

    def test_summary_mentions_skipped(self):
        env = _env(FOO="bar")
        result = alias_env(env, {"X": "MISSING"})
        assert "skipped" in result.summary()

    def test_is_changed_false_when_all_skipped(self):
        env = _env(FOO="bar")
        result = alias_env(env, {"X": "MISSING"})
        assert not result.is_changed

    def test_to_string_produces_env_lines(self):
        env = _env(ALPHA="1")
        result = alias_env(env, {"BETA": "ALPHA"})
        output = result.to_string()
        assert "BETA=1" in output
