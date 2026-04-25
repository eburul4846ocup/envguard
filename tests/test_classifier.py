"""Tests for envguard.classifier."""
from __future__ import annotations

import pytest

from envguard.classifier import ClassifyResult, classify_env


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# classify_env
# ---------------------------------------------------------------------------

def test_empty_env_returns_empty_result():
    result = classify_env({})
    assert result.total_keys == 0
    assert result.groups == {}


def test_secret_key_detected():
    result = classify_env({"DB_PASSWORD": "s3cr3t"})
    assert result.key_types["DB_PASSWORD"] == "secret"
    assert "DB_PASSWORD" in result.groups["secret"]


def test_token_key_classified_as_secret():
    result = classify_env({"GITHUB_TOKEN": "ghp_abc"})
    assert result.key_types["GITHUB_TOKEN"] == "secret"


def test_url_key_detected():
    result = classify_env({"DATABASE_URL": "postgres://localhost/db"})
    assert result.key_types["DATABASE_URL"] == "url"


def test_flag_key_detected():
    result = classify_env({"DEBUG": "true"})
    assert result.key_types["DEBUG"] == "flag"


def test_numeric_value_classified():
    result = classify_env({"PORT": "8080"})
    assert result.key_types["PORT"] == "numeric"


def test_negative_numeric_classified():
    result = classify_env({"OFFSET": "-5"})
    assert result.key_types["OFFSET"] == "numeric"


def test_plain_key_classified():
    result = classify_env({"APP_NAME": "myapp"})
    assert result.key_types["APP_NAME"] == "plain"


def test_multiple_categories():
    env = {
        "SECRET_KEY": "abc",
        "DATABASE_URL": "postgres://",
        "DEBUG": "false",
        "PORT": "3000",
        "APP_NAME": "envguard",
    }
    result = classify_env(env)
    assert result.key_types["SECRET_KEY"] == "secret"
    assert result.key_types["DATABASE_URL"] == "url"
    assert result.key_types["DEBUG"] == "flag"
    assert result.key_types["PORT"] == "numeric"
    assert result.key_types["APP_NAME"] == "plain"


def test_group_names_sorted():
    env = {"PORT": "9", "APP_NAME": "x", "SECRET_KEY": "s"}
    result = classify_env(env)
    assert result.group_names == sorted(result.group_names)


def test_total_keys_matches_env():
    env = {"A": "1", "B": "2", "C": "3"}
    result = classify_env(env)
    assert result.total_keys == 3


def test_summary_contains_total():
    result = classify_env({"PORT": "80"})
    assert "total=1" in result.summary()


def test_keys_within_group_are_sorted():
    env = {"Z_TOKEN": "z", "A_TOKEN": "a"}
    result = classify_env(env)
    assert result.groups["secret"] == ["A_TOKEN", "Z_TOKEN"]
