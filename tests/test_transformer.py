"""Tests for envguard.transformer."""
import pytest
from envguard.transformer import transform_env, TransformResult


def _env(**kwargs):
    return dict(kwargs)


def test_no_transforms_returns_unchanged():
    env = _env(FOO="bar", BAZ="qux")
    result = transform_env(env, [])
    assert result.data == env
    assert result.change_count == 0
    assert not result.is_changed


def test_summary_no_changes():
    result = transform_env({}, [])
    assert result.summary() == "No transformations applied."


def test_uppercase_values():
    env = _env(FOO="hello", BAR="world")
    result = transform_env(env, ["uppercase"])
    assert result.data == {"FOO": "HELLO", "BAR": "WORLD"}
    assert result.change_count == 2


def test_lowercase_values():
    env = _env(A="Hello", B="WORLD")
    result = transform_env(env, ["lowercase"])
    assert result.data["A"] == "hello"
    assert result.data["B"] == "world"


def test_strip_removes_whitespace():
    env = _env(KEY="  value  ")
    result = transform_env(env, ["strip"])
    assert result.data["KEY"] == "value"
    assert result.is_changed


def test_strip_no_change_if_clean():
    env = _env(KEY="value")
    result = transform_env(env, ["strip"])
    assert result.change_count == 0


def test_key_uppercase():
    env = {"foo": "bar", "baz": "qux"}
    result = transform_env(env, ["key_uppercase"])
    assert "FOO" in result.data
    assert "BAZ" in result.data
    assert result.is_changed


def test_multiple_transforms_applied_in_order():
    env = _env(KEY="  Hello  ")
    result = transform_env(env, ["strip", "lowercase"])
    assert result.data["KEY"] == "hello"


def test_custom_transform_fn():
    def prefix_values(k, v):
        return k, f"prefix_{v}"

    env = _env(A="one", B="two")
    result = transform_env(env, [prefix_values])
    assert result.data["A"] == "prefix_one"
    assert result.data["B"] == "prefix_two"


def test_unknown_builtin_raises():
    with pytest.raises(ValueError, match="Unknown built-in transform"):
        transform_env({"K": "v"}, ["nonexistent"])


def test_summary_with_changes():
    env = _env(X="hello")
    result = transform_env(env, ["uppercase"])
    assert "1 value(s) transformed" in result.summary()
