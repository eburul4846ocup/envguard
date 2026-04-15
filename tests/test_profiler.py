"""Unit tests for envguard.profiler."""
from __future__ import annotations

import pytest

from envguard.profiler import ProfileResult, profile_env


def _env(**kwargs: str):
    return dict(kwargs)


def test_empty_env_gives_zero_totals():
    result = profile_env({})
    assert result.total_keys == 0
    assert result.summary()["total"] == 0


def test_total_keys_count():
    env = _env(A="1", B="2", C="3")
    result = profile_env(env)
    assert result.total_keys == 3


def test_empty_value_classified():
    result = profile_env({"EMPTY_VAR": "", "SPACE_VAR": "   "})
    assert "EMPTY_VAR" in result.empty_values
    assert "SPACE_VAR" in result.empty_values
    assert result.summary()["empty"] == 2


def test_secret_key_detected():
    env = _env(DB_PASSWORD="s3cr3t", API_KEY="abc123", NAME="alice")
    result = profile_env(env)
    assert "DB_PASSWORD" in result.secret_keys
    assert "API_KEY" in result.secret_keys
    assert "NAME" not in result.secret_keys


def test_url_value_classified():
    env = _env(BASE_URL="https://example.com", OTHER="hello")
    result = profile_env(env)
    assert "BASE_URL" in result.url_values
    assert "OTHER" not in result.url_values


def test_boolean_value_classified():
    for val in ("true", "false", "True", "1", "0", "yes", "no"):
        result = profile_env({"FLAG": val})
        assert "FLAG" in result.boolean_values, f"Expected boolean for value {val!r}"


def test_numeric_value_classified():
    for val in ("42", "-7", "3.14"):
        result = profile_env({"NUM": val})
        assert "NUM" in result.numeric_values, f"Expected numeric for value {val!r}"


def test_plain_value_classified():
    result = profile_env({"APP_NAME": "myapp"})
    assert "APP_NAME" in result.plain_values


def test_summary_keys_present():
    result = profile_env(_env(X="hello"))
    keys = result.summary().keys()
    for expected in ("total", "empty", "secrets", "urls", "booleans", "numeric", "plain"):
        assert expected in keys


def test_secret_key_also_categorised_by_value():
    """A secret key with a URL value appears in both secret_keys and url_values."""
    env = _env(AUTH_TOKEN="https://token.example.com/v1")
    result = profile_env(env)
    assert "AUTH_TOKEN" in result.secret_keys
    assert "AUTH_TOKEN" in result.url_values
