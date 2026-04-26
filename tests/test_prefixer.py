"""Tests for envguard.prefixer."""
from __future__ import annotations

import pytest

from envguard.prefixer import PrefixResult, add_prefix, remove_prefix


@pytest.fixture()
def _env() -> dict:
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "s3cr3t",
        "DEBUG": "true",
    }


# ---------------------------------------------------------------------------
# add_prefix
# ---------------------------------------------------------------------------

class TestAddPrefix:
    def test_all_keys_are_prefixed(self, _env):
        result = add_prefix(_env, "APP_")
        assert "APP_DATABASE_URL" in result.env
        assert "APP_SECRET_KEY" in result.env
        assert "APP_DEBUG" in result.env

    def test_original_keys_absent(self, _env):
        result = add_prefix(_env, "APP_")
        for key in _env:
            assert key not in result.env

    def test_values_preserved(self, _env):
        result = add_prefix(_env, "APP_")
        assert result.env["APP_DATABASE_URL"] == "postgres://localhost/db"

    def test_change_count_equals_key_count(self, _env):
        result = add_prefix(_env, "APP_")
        assert result.change_count == len(_env)

    def test_is_changed_true(self, _env):
        result = add_prefix(_env, "APP_")
        assert result.is_changed is True

    def test_empty_env_returns_empty_result(self):
        result = add_prefix({}, "APP_")
        assert result.env == {}
        assert result.change_count == 0
        assert result.is_changed is False

    def test_skip_existing_true_leaves_already_prefixed_keys(self):
        env = {"APP_KEY": "value", "OTHER": "x"}
        result = add_prefix(env, "APP_", skip_existing=True)
        assert "APP_KEY" in result.env
        assert "APP_OTHER" in result.env
        assert result.skipped_keys == ["APP_KEY"]
        assert result.changed_keys == ["OTHER"]

    def test_skip_existing_false_double_prefixes(self):
        env = {"APP_KEY": "value"}
        result = add_prefix(env, "APP_", skip_existing=False)
        assert "APP_APP_KEY" in result.env
        assert result.change_count == 1

    def test_summary_no_changes(self):
        result = add_prefix({}, "X_")
        assert result.summary() == "No keys were modified."

    def test_summary_with_changes(self, _env):
        result = add_prefix(_env, "APP_")
        assert "3 key(s) modified" in result.summary()

    def test_to_string_sorted(self, _env):
        result = add_prefix(_env, "APP_")
        lines = result.to_string().strip().splitlines()
        keys = [line.split("=")[0] for line in lines]
        assert keys == sorted(keys)


# ---------------------------------------------------------------------------
# remove_prefix
# ---------------------------------------------------------------------------

class TestRemovePrefix:
    def test_matching_keys_stripped(self):
        env = {"APP_FOO": "1", "APP_BAR": "2"}
        result = remove_prefix(env, "APP_")
        assert "FOO" in result.env
        assert "BAR" in result.env

    def test_non_matching_keys_skipped(self):
        env = {"APP_FOO": "1", "OTHER": "2"}
        result = remove_prefix(env, "APP_")
        assert "OTHER" in result.env
        assert result.skipped_keys == ["OTHER"]

    def test_values_preserved_after_strip(self):
        env = {"APP_FOO": "hello"}
        result = remove_prefix(env, "APP_")
        assert result.env["FOO"] == "hello"

    def test_change_count_only_matching(self):
        env = {"APP_A": "1", "APP_B": "2", "PLAIN": "3"}
        result = remove_prefix(env, "APP_")
        assert result.change_count == 2

    def test_empty_env(self):
        result = remove_prefix({}, "APP_")
        assert result.env == {}
        assert result.is_changed is False

    def test_no_matching_keys_is_not_changed(self):
        env = {"FOO": "1", "BAR": "2"}
        result = remove_prefix(env, "APP_")
        assert result.is_changed is False
        assert len(result.skipped_keys) == 2
