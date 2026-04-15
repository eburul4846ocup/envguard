"""Tests for envguard.grouper."""
import pytest
from envguard.grouper import GroupResult, group_env


def _env(**kwargs: str):
    return dict(kwargs)


class TestGroupEnvDefaults:
    def test_empty_env_returns_empty_result(self):
        result = group_env({})
        assert result.groups == {}
        assert result.ungrouped == {}
        assert result.total_keys == 0

    def test_keys_without_separator_go_to_ungrouped(self):
        env = _env(DEBUG="true", PORT="8080")
        result = group_env(env)
        assert result.ungrouped == {"DEBUG": "true", "PORT": "8080"}
        assert result.groups == {}

    def test_keys_with_prefix_are_grouped(self):
        env = _env(DB_HOST="localhost", DB_PORT="5432", APP_NAME="envguard")
        result = group_env(env)
        assert "DB" in result.groups
        assert "APP" in result.groups
        assert result.groups["DB"] == {"DB_HOST": "localhost", "DB_PORT": "5432"}
        assert result.groups["APP"] == {"APP_NAME": "envguard"}

    def test_short_prefix_goes_to_ungrouped(self):
        # prefix "A" is only 1 char, below min_prefix_length=2
        env = _env(A_KEY="val")
        result = group_env(env)
        assert result.ungrouped == {"A_KEY": "val"}
        assert result.groups == {}

    def test_min_prefix_length_override(self):
        env = _env(A_KEY="val")
        result = group_env(env, min_prefix_length=1)
        assert "A" in result.groups

    def test_total_keys_counts_all(self):
        env = _env(DB_HOST="h", DB_PORT="p", DEBUG="true")
        result = group_env(env)
        assert result.total_keys == 3

    def test_group_names_are_sorted(self):
        env = _env(Z_KEY="z", A_KEY="a", M_KEY="m")
        result = group_env(env)
        assert result.group_names == ["A", "M", "Z"]


class TestGroupEnvKnownPrefixes:
    def test_only_known_prefixes_are_grouped(self):
        env = _env(DB_HOST="localhost", REDIS_URL="redis://", APP_NAME="eg")
        result = group_env(env, known_prefixes=["DB", "REDIS"])
        assert "DB" in result.groups
        assert "REDIS" in result.groups
        assert "APP" not in result.groups
        assert "APP_NAME" in result.ungrouped

    def test_unknown_prefix_keys_go_to_ungrouped(self):
        env = _env(FOO_BAR="baz")
        result = group_env(env, known_prefixes=["DB"])
        assert result.ungrouped == {"FOO_BAR": "baz"}

    def test_known_prefix_case_insensitive_match(self):
        env = _env(DB_HOST="localhost")
        result = group_env(env, known_prefixes=["db"])
        assert "DB" in result.groups


class TestGroupResultSummary:
    def test_summary_contains_group_count(self):
        env = _env(DB_HOST="h", APP_NAME="n")
        result = group_env(env)
        summary = result.summary()
        assert "Groups: 2" in summary

    def test_summary_contains_ungrouped_count(self):
        env = _env(DEBUG="true")
        result = group_env(env)
        assert "Ungrouped: 1" in result.summary()

    def test_summary_lists_group_names(self):
        env = _env(DB_HOST="h", DB_PORT="p")
        result = group_env(env)
        assert "[DB]" in result.summary()
