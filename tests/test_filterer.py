"""Tests for envguard.filterer."""
import pytest
from envguard.filterer import filter_env, FilterResult


@pytest.fixture()
def _env() -> dict:
    return {
        "AWS_ACCESS_KEY": "AKIA123",
        "AWS_SECRET": "secret",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "",
        "APP_DEBUG": "true",
        "PORT": "8080",
    }


def test_no_criteria_matches_everything(_env):
    result = filter_env(_env)
    assert result.match_count == len(_env)
    assert result.excluded_count == 0


def test_prefix_filter_matches_aws_keys(_env):
    result = filter_env(_env, prefixes=["AWS_"])
    assert set(result.matched.keys()) == {"AWS_ACCESS_KEY", "AWS_SECRET"}


def test_prefix_filter_excludes_non_matching(_env):
    result = filter_env(_env, prefixes=["AWS_"])
    assert "DB_HOST" in result.excluded
    assert "PORT" in result.excluded


def test_pattern_filter_matches_by_regex(_env):
    result = filter_env(_env, patterns=[r"^DB_"])
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PASSWORD"}


def test_multiple_prefixes_union(_env):
    result = filter_env(_env, prefixes=["AWS_", "DB_"])
    assert "AWS_ACCESS_KEY" in result.matched
    assert "DB_HOST" in result.matched
    assert "PORT" in result.excluded


def test_exclude_empty_removes_blank_values(_env):
    result = filter_env(_env, prefixes=["DB_"], exclude_empty=True)
    assert "DB_HOST" in result.matched
    assert "DB_PASSWORD" not in result.matched


def test_invert_flips_match_and_excluded(_env):
    result = filter_env(_env, prefixes=["AWS_"], invert=True)
    assert "AWS_ACCESS_KEY" not in result.matched
    assert "DB_HOST" in result.matched


def test_match_count_property(_env):
    result = filter_env(_env, prefixes=["APP_"])
    assert result.match_count == 1


def test_is_empty_when_nothing_matches(_env):
    result = filter_env(_env, prefixes=["NONEXISTENT_"])
    assert result.is_empty


def test_summary_string(_env):
    result = filter_env(_env, prefixes=["AWS_"])
    s = result.summary()
    assert "Matched" in s
    assert "excluded" in s


def test_empty_env_returns_empty_result():
    result = filter_env({})
    assert result.match_count == 0
    assert result.excluded_count == 0
    assert result.is_empty


def test_pattern_case_insensitive(_env):
    result = filter_env(_env, patterns=[r"^aws_"])
    assert "AWS_ACCESS_KEY" in result.matched
    assert "AWS_SECRET" in result.matched
