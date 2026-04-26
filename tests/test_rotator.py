"""Tests for envguard.rotator."""
from datetime import date

import pytest

from envguard.rotator import RotationIssue, RotationResult, rotate_env, _parse_date


TODAY = date(2024, 6, 1)


def _env(**kwargs):
    return {k: v for k, v in kwargs.items()}


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

def test_parse_date_valid():
    assert _parse_date("2024-01-15") == date(2024, 1, 15)


def test_parse_date_with_whitespace():
    assert _parse_date(" 2024-01-15 ") == date(2024, 1, 15)


def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None


def test_parse_date_empty_string_returns_none():
    assert _parse_date("") is None


# ---------------------------------------------------------------------------
# rotate_env — clean cases
# ---------------------------------------------------------------------------

def test_clean_env_no_secret_keys():
    env = _env(DEBUG="true", HOST="localhost")
    result = rotate_env(env, today=TODAY)
    assert result.is_clean
    assert result.checked == 0


def test_fresh_secret_key_is_clean():
    env = _env(API_KEY="abc123")
    pins = {"API_KEY": "2024-05-01"}  # 31 days old — under 90
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert result.is_clean
    assert result.checked == 1


def test_summary_all_clean():
    env = _env(DB_PASSWORD="secret")
    pins = {"DB_PASSWORD": "2024-05-15"}
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert "within rotation policy" in result.summary()


# ---------------------------------------------------------------------------
# rotate_env — issue cases
# ---------------------------------------------------------------------------

def test_missing_pin_date_raises_issue():
    env = _env(API_SECRET="value")
    result = rotate_env(env, pin_dates={}, today=TODAY)
    assert not result.is_clean
    assert result.issue_count == 1
    assert "No rotation date" in result.issues[0].reason


def test_invalid_pin_date_format_raises_issue():
    env = _env(APP_TOKEN="value")
    result = rotate_env(env, pin_dates={"APP_TOKEN": "01/01/2024"}, today=TODAY)
    assert not result.is_clean
    assert "Invalid date format" in result.issues[0].reason


def test_stale_key_raises_issue():
    env = _env(DB_PASSWORD="old")
    pins = {"DB_PASSWORD": "2024-01-01"}  # 152 days old
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert not result.is_clean
    issue = result.issues[0]
    assert issue.age_days == 152
    assert "exceeds" in issue.reason


def test_exactly_at_limit_is_clean():
    env = _env(API_KEY="val")
    pins = {"API_KEY": "2024-03-03"}  # exactly 90 days before 2024-06-01
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert result.is_clean


def test_one_over_limit_is_issue():
    env = _env(API_KEY="val")
    pins = {"API_KEY": "2024-03-02"}  # 91 days
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert not result.is_clean


def test_multiple_secrets_mixed_result():
    env = _env(API_KEY="v1", DB_PASSWORD="v2", HOST="localhost")
    pins = {
        "API_KEY": "2024-05-01",   # fresh
        "DB_PASSWORD": "2023-01-01",  # very stale
    }
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert result.checked == 2
    assert result.issue_count == 1
    assert result.issues[0].key == "DB_PASSWORD"


def test_issue_str_includes_age():
    issue = RotationIssue(key="MY_KEY", pinned_date=date(2024, 1, 1), age_days=152, reason="Too old.")
    assert "MY_KEY" in str(issue)
    assert "152d" in str(issue)


def test_summary_reports_issue_count():
    env = _env(API_SECRET="x")
    result = rotate_env(env, today=TODAY)
    assert "1 rotation issue" in result.summary()


def test_custom_max_age_respected():
    env = _env(API_KEY="val")
    pins = {"API_KEY": "2024-05-25"}  # 7 days old
    result = rotate_env(env, pin_dates=pins, max_age_days=5, today=TODAY)
    assert not result.is_clean
