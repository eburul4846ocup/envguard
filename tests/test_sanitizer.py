"""Tests for envguard.sanitizer."""
import pytest
from envguard.sanitizer import sanitize_env, SanitizeResult


def _env(**kwargs: str):
    return dict(kwargs)


def test_clean_values_return_unchanged():
    env = _env(FOO="bar", BAZ="hello world")
    result = sanitize_env(env)
    assert result.sanitized == env
    assert not result.is_changed
    assert result.change_count == 0


def test_null_byte_is_removed():
    env = _env(SECRET="abc\x00def")
    result = sanitize_env(env, strip_null=True)
    assert result.sanitized["SECRET"] == "abcdef"
    assert "SECRET" in result.changed_keys


def test_strip_null_disabled_preserves_null():
    env = _env(KEY="val\x00ue")
    result = sanitize_env(env, strip_null=False)
    assert result.sanitized["KEY"] == "val\x00ue"
    assert not result.is_changed


def test_control_char_removed():
    env = _env(MSG="hello\x01world")
    result = sanitize_env(env, strip_ctrl=True)
    assert result.sanitized["MSG"] == "helloworld"
    assert "MSG" in result.changed_keys


def test_tab_and_newline_preserved_by_ctrl_strip():
    # tab (\t = 0x09) and newline (\n = 0x0a) are excluded from ctrl stripping
    env = _env(VAL="line1\nline2", TAB="col1\tcol2")
    result = sanitize_env(env, strip_ctrl=True)
    assert result.sanitized["VAL"] == "line1\nline2"
    assert result.sanitized["TAB"] == "col1\tcol2"
    assert not result.is_changed


def test_collapse_spaces_disabled_by_default():
    env = _env(VAL="hello   world")
    result = sanitize_env(env)
    assert result.sanitized["VAL"] == "hello   world"
    assert not result.is_changed


def test_collapse_spaces_enabled():
    env = _env(VAL="hello   world", OTHER="a  b  c")
    result = sanitize_env(env, collapse_spaces=True)
    assert result.sanitized["VAL"] == "hello world"
    assert result.sanitized["OTHER"] == "a b c"
    assert set(result.changed_keys) == {"VAL", "OTHER"}


def test_summary_no_changes():
    env = _env(A="clean")
    result = sanitize_env(env)
    assert "no sanitization" in result.summary()


def test_summary_with_changes():
    env = _env(KEY="bad\x00val")
    result = sanitize_env(env)
    assert "1" in result.summary()
    assert "KEY" in result.summary()


def test_to_string_output():
    env = _env(FOO="bar", BAZ="qux")
    result = sanitize_env(env)
    output = result.to_string()
    assert "FOO=bar" in output
    assert "BAZ=qux" in output


def test_empty_env_returns_empty_result():
    result = sanitize_env({})
    assert result.sanitized == {}
    assert not result.is_changed


def test_multiple_issues_in_single_value():
    env = _env(VAL="\x00\x01clean")
    result = sanitize_env(env, strip_null=True, strip_ctrl=True)
    assert result.sanitized["VAL"] == "clean"
    assert result.is_changed
