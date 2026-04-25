"""Tests for envguard.trimmer."""
import pytest

from envguard.trimmer import TrimResult, trim_env


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# trim_env – core behaviour
# ---------------------------------------------------------------------------

def test_no_whitespace_returns_unchanged():
    env = _env(HOST="localhost", PORT="5432")
    result = trim_env(env)
    assert result.trimmed == env
    assert result.change_count == 0
    assert not result.is_changed


def test_leading_space_is_removed():
    env = _env(HOST="  localhost")
    result = trim_env(env)
    assert result.trimmed["HOST"] == "localhost"
    assert "HOST" in result.changed_keys


def test_trailing_space_is_removed():
    env = _env(PORT="5432   ")
    result = trim_env(env)
    assert result.trimmed["PORT"] == "5432"
    assert "PORT" in result.changed_keys


def test_both_sides_trimmed():
    env = _env(NAME="  my-app  ")
    result = trim_env(env)
    assert result.trimmed["NAME"] == "my-app"


def test_tab_characters_trimmed():
    env = _env(KEY="\tvalue\t")
    result = trim_env(env)
    assert result.trimmed["KEY"] == "value"


def test_empty_value_stays_empty():
    env = _env(EMPTY="")
    result = trim_env(env)
    assert result.trimmed["EMPTY"] == ""
    assert result.change_count == 0


def test_whitespace_only_value_becomes_empty():
    env = _env(BLANK="   ")
    result = trim_env(env)
    assert result.trimmed["BLANK"] == ""
    assert "BLANK" in result.changed_keys


def test_multiple_keys_only_dirty_ones_listed():
    env = _env(A="clean", B=" dirty ", C="\talso dirty")
    result = trim_env(env)
    assert result.change_count == 2
    assert "B" in result.changed_keys
    assert "C" in result.changed_keys
    assert "A" not in result.changed_keys


def test_original_is_preserved():
    env = _env(HOST="  localhost")
    result = trim_env(env)
    assert result.original["HOST"] == "  localhost"


def test_empty_env_returns_empty_result():
    result = trim_env({})
    assert result.trimmed == {}
    assert result.change_count == 0
    assert not result.is_changed


# ---------------------------------------------------------------------------
# TrimResult helpers
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    result = trim_env(_env(KEY="value"))
    assert result.summary() == "No values required trimming."


def test_summary_with_changes():
    result = trim_env(_env(KEY=" value "))
    assert "1 value(s) trimmed" in result.summary()
    assert "KEY" in result.summary()


def test_to_string_sorted_output():
    env = _env(Z=" z ", A=" a ")
    result = trim_env(env)
    lines = result.to_string().splitlines()
    assert lines[0].startswith("A=")
    assert lines[1].startswith("Z=")


def test_to_string_empty_env():
    result = trim_env({})
    assert result.to_string() == ""


def test_changed_keys_are_sorted():
    env = _env(Z=" z ", A=" a ", M=" m ")
    result = trim_env(env)
    assert result.changed_keys == sorted(result.changed_keys)
