"""Tests for envguard.summarizer."""
import pytest
from envguard.summarizer import summarize_env, SummaryResult


def _env(**kwargs):
    return dict(kwargs)


def test_empty_env_returns_zero_totals():
    result = summarize_env({})
    assert result.total_keys == 0
    assert result.empty_count() == 0
    assert result.secret_count() == 0
    assert result.plain_count() == 0


def test_total_keys_counted():
    result = summarize_env(_env(FOO="bar", BAZ="qux"))
    assert result.total_keys == 2


def test_secret_key_detected():
    result = summarize_env(_env(DB_PASSWORD="secret123", HOST="localhost"))
    assert "DB_PASSWORD" in result.secret_keys
    assert "HOST" not in result.secret_keys


def test_plain_key_classified():
    result = summarize_env(_env(APP_NAME="envguard", DEBUG="true"))
    assert "APP_NAME" in result.plain_keys
    assert "DEBUG" in result.plain_keys


def test_empty_value_detected():
    result = summarize_env(_env(MISSING="", PRESENT="value"))
    assert "MISSING" in result.empty_keys
    assert "PRESENT" not in result.empty_keys


def test_secret_key_with_empty_value_appears_in_both():
    result = summarize_env(_env(API_KEY=""))
    assert "API_KEY" in result.secret_keys
    assert "API_KEY" in result.empty_keys


def test_summary_string_contains_counts():
    result = summarize_env(_env(DB_PASSWORD="x", HOST="localhost", EMPTY=""))
    text = result.summary()
    assert "Total keys" in text
    assert "Secret keys" in text
    assert "Empty keys" in text


def test_keys_are_sorted_in_results():
    result = summarize_env(_env(Z_TOKEN="t", A_TOKEN="t", M_TOKEN="t"))
    assert result.secret_keys == sorted(result.secret_keys)


def test_api_key_hint_detected():
    result = summarize_env(_env(STRIPE_API_KEY="sk_live_abc"))
    assert "STRIPE_API_KEY" in result.secret_keys


def test_plain_count_excludes_secret_keys():
    result = summarize_env(_env(SECRET_KEY="abc", APP_ENV="prod"))
    assert result.plain_count() == 1
    assert "APP_ENV" in result.plain_keys
