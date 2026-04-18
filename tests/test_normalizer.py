"""Tests for envguard.normalizer."""
import pytest
from envguard.normalizer import normalize_env, NormalizeResult


def _env(**kwargs):
    return dict(kwargs)


def test_no_changes_when_already_clean():
    env = _env(HOST="localhost", PORT="5432")
    result = normalize_env(env)
    assert not result.is_changed
    assert result.change_count == 0
    assert result.normalized == env


def test_strips_double_quotes():
    env = _env(NAME='"alice"')
    result = normalize_env(env)
    assert result.normalized["NAME"] == "alice"
    assert result.change_count == 1


def test_strips_single_quotes():
    env = _env(NAME="'bob'")
    result = normalize_env(env)
    assert result.normalized["NAME"] == "bob"


def test_no_strip_quotes_option_preserves_quotes():
    env = _env(NAME='"alice"')
    result = normalize_env(env, strip_quotes=False)
    assert result.normalized["NAME"] == '"alice"'
    assert not result.is_changed


def test_lowercase_true_value():
    env = _env(DEBUG="True")
    result = normalize_env(env)
    assert result.normalized["DEBUG"] == "true"
    assert result.change_count == 1


def test_lowercase_false_value():
    env = _env(ENABLED="FALSE")
    result = normalize_env(env)
    assert result.normalized["ENABLED"] == "false"


def test_lowercase_yes_no():
    env = _env(FEATURE="YES", LEGACY="NO")
    result = normalize_env(env)
    assert result.normalized["FEATURE"] == "yes"
    assert result.normalized["LEGACY"] == "no"


def test_no_lowercase_booleans_option():
    env = _env(DEBUG="True")
    result = normalize_env(env, lowercase_booleans=False)
    assert result.normalized["DEBUG"] == "True"
    assert not result.is_changed


def test_summary_no_changes():
    result = normalize_env(_env(A="1"))
    assert result.summary() == "No normalization changes."


def test_summary_with_changes():
    result = normalize_env(_env(FLAG="True"))
    s = result.summary()
    assert "1 value(s) normalized" in s
    assert "FLAG" in s


def test_to_string_sorted():
    env = _env(Z="1", A="2")
    result = normalize_env(env)
    lines = result.to_string().strip().splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_whitespace_trimmed_from_value():
    env = {"KEY": "  hello  "}
    result = normalize_env(env)
    assert result.normalized["KEY"] == "hello"
    assert result.change_count == 1


def test_changes_record_old_and_new():
    env = _env(MODE="'prod'")
    result = normalize_env(env)
    key, old, new = result.changes[0]
    assert key == "MODE"
    assert old == "'prod'"
    assert new == "prod"
