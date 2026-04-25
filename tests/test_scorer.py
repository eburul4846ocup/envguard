"""Tests for envguard.scorer."""
from __future__ import annotations

import pytest

from envguard.scorer import ScoreResult, score_env


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


def test_empty_env_returns_perfect_score():
    result = score_env({})
    assert result.score == 100
    assert result.grade == "A"
    assert result.total_keys == 0


def test_clean_env_returns_perfect_score():
    result = score_env({"APP_NAME": "myapp", "PORT": "8080"})
    assert result.score == 100
    assert result.grade == "A"
    assert len(result.penalties) == 0


def test_empty_value_adds_penalty():
    result = score_env({"APP_NAME": ""})
    assert result.score < 100
    assert any("empty_value" in p for p in result.penalties)


def test_plain_secret_value_adds_penalty():
    result = score_env({"API_KEY": "super-secret-123"})
    assert any("secret_plain" in p for p in result.penalties)


def test_lowercase_key_adds_penalty_when_required():
    result = score_env({"app_name": "foo"}, require_uppercase=True)
    assert any("no_uppercase" in p for p in result.penalties)


def test_lowercase_key_no_penalty_when_suppressed():
    result = score_env({"app_name": "foo"}, require_uppercase=False)
    assert not any("no_uppercase" in p for p in result.penalties)


def test_placeholder_value_adds_penalty():
    result = score_env({"DB_URL": "CHANGE_ME"})
    assert any("placeholder_value" in p for p in result.penalties)


def test_angle_bracket_placeholder_adds_penalty():
    result = score_env({"DB_HOST": "<your-host>"}, require_uppercase=True)
    assert any("placeholder_value" in p for p in result.penalties)


def test_very_long_value_adds_penalty():
    result = score_env({"CERT": "x" * 600})
    assert any("very_long_value" in p for p in result.penalties)


def test_score_never_goes_below_zero():
    env = {
        "api_key": "",
        "db_password": "CHANGE_ME",
        "token": "raw-token",
        "secret": "x" * 600,
    }
    result = score_env(env, require_uppercase=True)
    assert result.score >= 0


def test_grade_boundaries():
    assert ScoreResult(score=95, total_keys=1).grade == "A"
    assert ScoreResult(score=80, total_keys=1).grade == "B"
    assert ScoreResult(score=65, total_keys=1).grade == "C"
    assert ScoreResult(score=45, total_keys=1).grade == "D"
    assert ScoreResult(score=30, total_keys=1).grade == "F"


def test_total_keys_reported():
    result = score_env({"A": "1", "B": "2", "C": "3"})
    assert result.total_keys == 3


def test_summary_contains_score_and_grade():
    result = score_env({"APP": "prod"})
    s = result.summary()
    assert "100" in s
    assert "A" in s
