"""Tests for envguard.caster."""
import pytest
from envguard.caster import cast_env, CastResult


@pytest.fixture()
def _env():
    return {
        "PORT": "8080",
        "RATE": "3.14",
        "DEBUG": "true",
        "TAGS": "alpha,beta,gamma",
        "NAME": "envguard",
    }


def test_no_casts_returns_unchanged(_env):
    result = cast_env(_env, {})
    assert result.env == _env
    assert result.change_count == 0
    assert not result.is_changed


def test_cast_int_converts_value(_env):
    result = cast_env(_env, {"PORT": "int"})
    assert result.env["PORT"] == 8080
    assert isinstance(result.env["PORT"], int)
    assert "PORT" in result.changed_keys


def test_cast_float_converts_value(_env):
    result = cast_env(_env, {"RATE": "float"})
    assert result.env["RATE"] == pytest.approx(3.14)
    assert isinstance(result.env["RATE"], float)


def test_cast_bool_true(_env):
    result = cast_env(_env, {"DEBUG": "bool"})
    assert result.env["DEBUG"] is True


def test_cast_bool_false():
    result = cast_env({"VERBOSE": "0"}, {"VERBOSE": "bool"})
    assert result.env["VERBOSE"] is False


def test_cast_bool_invalid_records_error():
    result = cast_env({"FLAG": "maybe"}, {"FLAG": "bool"})
    assert "FLAG" in result.errors
    assert result.env["FLAG"] == "maybe"  # original preserved
    assert not result.is_clean


def test_cast_list_splits_csv(_env):
    result = cast_env(_env, {"TAGS": "list"})
    assert result.env["TAGS"] == ["alpha", "beta", "gamma"]


def test_cast_str_is_noop(_env):
    result = cast_env(_env, {"NAME": "str"})
    assert result.env["NAME"] == "envguard"
    assert result.change_count == 0


def test_missing_key_in_casts_is_ignored(_env):
    result = cast_env(_env, {"MISSING_KEY": "int"})
    assert "MISSING_KEY" not in result.env
    assert result.change_count == 0


def test_unknown_target_type_records_error():
    result = cast_env({"X": "1"}, {"X": "uuid"})
    assert "X" in result.errors
    assert "Unknown target type" in result.errors["X"]


def test_summary_all_clean(_env):
    result = cast_env(_env, {"PORT": "int", "RATE": "float"})
    s = result.summary()
    assert "cast" in s
    assert "error" not in s


def test_summary_with_errors():
    result = cast_env({"X": "bad"}, {"X": "int"})
    s = result.summary()
    assert "error" in s


def test_is_changed_false_when_no_casts(_env):
    result = cast_env(_env, {})
    assert not result.is_changed


def test_multiple_casts_all_applied(_env):
    result = cast_env(_env, {"PORT": "int", "DEBUG": "bool", "TAGS": "list"})
    assert result.env["PORT"] == 8080
    assert result.env["DEBUG"] is True
    assert result.env["TAGS"] == ["alpha", "beta", "gamma"]
    assert result.change_count == 3
