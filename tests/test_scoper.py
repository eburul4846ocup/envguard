"""Tests for envguard.scoper."""
import pytest
from envguard.scoper import scope_env, ScopeResult


@pytest.fixture()
def _env() -> dict:
    return {
        "AWS_ACCESS_KEY_ID": "AKIA123",
        "AWS_SECRET_ACCESS_KEY": "secret",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DEBUG": "true",
    }


def test_no_filter_returns_all_keys(_env):
    result = scope_env(_env)
    assert result.scoped == _env
    assert result.excluded == {}
    assert result.key_count == 5
    assert result.excluded_count == 0


def test_prefix_filter_returns_matching_keys(_env):
    result = scope_env(_env, prefix="AWS_")
    assert set(result.scoped.keys()) == {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}
    assert "DB_HOST" in result.excluded
    assert result.key_count == 2


def test_prefix_excludes_non_matching(_env):
    result = scope_env(_env, prefix="DB_")
    assert set(result.scoped.keys()) == {"DB_HOST", "DB_PORT"}
    assert result.excluded_count == 3


def test_keys_filter_returns_exact_keys(_env):
    result = scope_env(_env, keys=["DEBUG", "DB_HOST"])
    assert set(result.scoped.keys()) == {"DEBUG", "DB_HOST"}
    assert result.key_count == 2


def test_missing_key_in_keys_filter_is_ignored(_env):
    result = scope_env(_env, keys=["NONEXISTENT", "DEBUG"])
    assert set(result.scoped.keys()) == {"DEBUG"}


def test_prefix_and_keys_combined_union(_env):
    result = scope_env(_env, prefix="AWS_", keys=["DEBUG"])
    assert "AWS_ACCESS_KEY_ID" in result.scoped
    assert "DEBUG" in result.scoped
    assert result.key_count == 3


def test_case_insensitive_prefix(_env):
    result = scope_env(_env, prefix="aws_", case_sensitive=False)
    assert set(result.scoped.keys()) == {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}


def test_case_insensitive_keys(_env):
    result = scope_env(_env, keys=["debug"], case_sensitive=False)
    assert "DEBUG" in result.scoped


def test_summary_contains_counts(_env):
    result = scope_env(_env, prefix="DB_")
    s = result.summary()
    assert "scoped=2" in s
    assert "excluded=3" in s
    assert "prefix='DB_'" in s


def test_to_string_sorted_output(_env):
    result = scope_env(_env, prefix="DB_")
    lines = result.to_string().splitlines()
    keys = [l.split("=")[0] for l in lines]
    assert keys == sorted(keys)


def test_to_string_strip_prefix(_env):
    result = scope_env(_env, prefix="AWS_")
    output = result.to_string(strip_prefix=True)
    assert "ACCESS_KEY_ID=AKIA123" in output
    assert "AWS_" not in output


def test_to_string_no_strip_prefix_keeps_prefix(_env):
    result = scope_env(_env, prefix="AWS_")
    output = result.to_string(strip_prefix=False)
    assert "AWS_ACCESS_KEY_ID=AKIA123" in output


def test_empty_env_returns_empty_result():
    result = scope_env({}, prefix="APP_")
    assert result.scoped == {}
    assert result.excluded == {}
    assert result.key_count == 0
