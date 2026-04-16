"""Tests for envguard.formatter."""
import pytest
from envguard.formatter import format_env, FormatResult


def _env(**kwargs):
    return dict(kwargs)


def test_basic_format_no_quotes():
    result = format_env(_env(FOO="bar", BAZ="qux"))
    assert "FOO=bar" in result.formatted_lines
    assert "BAZ=qux" in result.formatted_lines


def test_quote_values_wraps_in_double_quotes():
    result = format_env(_env(KEY="value"), quote_values=True)
    assert 'KEY="value"' in result.formatted_lines


def test_quote_values_does_not_double_quote():
    result = format_env({"KEY": '"already"'}, quote_values=True)
    assert 'KEY="already"' in result.formatted_lines


def test_sort_keys_orders_alphabetically():
    result = format_env(_env(ZEBRA="1", ALPHA="2", MIDDLE="3"), sort_keys=True)
    assert result.formatted_lines == ["ALPHA=2", "MIDDLE=3", "ZEBRA=1"]


def test_no_sort_preserves_insertion_order():
    env = {"ZEBRA": "1", "ALPHA": "2"}
    result = format_env(env, sort_keys=False)
    assert result.formatted_lines[0] == "ZEBRA=1"
    assert result.formatted_lines[1] == "ALPHA=2"


def test_is_changed_false_when_identical():
    lines = ["FOO=bar\n", "BAZ=qux\n"]
    result = format_env({"FOO": "bar", "BAZ": "qux"}, original_lines=lines)
    assert not result.is_changed


def test_is_changed_true_when_different():
    lines = ["FOO=old\n"]
    result = format_env({"FOO": "new"}, original_lines=lines)
    assert result.is_changed
    assert result.changes >= 1


def test_to_string_ends_with_newline():
    result = format_env(_env(A="1"))
    assert result.to_string().endswith("\n")


def test_summary_no_changes():
    result = format_env(_env(A="1"), original_lines=["A=1\n"])
    assert "no changes" in result.summary()


def test_summary_with_changes():
    result = format_env(_env(A="new"), original_lines=["A=old\n"])
    assert "reformatted" in result.summary()


def test_empty_env_produces_empty_lines():
    result = format_env({})
    assert result.formatted_lines == []
    assert not result.is_changed
