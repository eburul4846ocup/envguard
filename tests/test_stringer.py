"""Tests for envguard.stringer."""
import pytest
from envguard.stringer import stringify_env, StringifyResult


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# StringifyResult helpers
# ---------------------------------------------------------------------------

def test_is_empty_on_empty_result():
    r = StringifyResult(lines=[], key_count=0)
    assert r.is_empty()


def test_is_not_empty_when_keys_present():
    r = StringifyResult(lines=["A=1"], key_count=1)
    assert not r.is_empty()


def test_to_string_joins_lines():
    r = StringifyResult(lines=["A=1", "B=2"], key_count=2)
    assert r.to_string() == "A=1\nB=2"


def test_summary_contains_count_and_format():
    r = StringifyResult(lines=["A=1"], key_count=1, format="dotenv")
    assert "1" in r.summary()
    assert "dotenv" in r.summary()


# ---------------------------------------------------------------------------
# stringify_env – basic
# ---------------------------------------------------------------------------

def test_empty_env_returns_empty_result():
    result = stringify_env({})
    assert result.is_empty()
    assert result.lines == []


def test_single_key_rendered():
    result = stringify_env({"FOO": "bar"})
    assert result.lines == ["FOO=bar"]
    assert result.key_count == 1


def test_keys_sorted_by_default():
    env = {"ZEBRA": "z", "ALPHA": "a", "MIDDLE": "m"}
    result = stringify_env(env)
    assert result.lines[0].startswith("ALPHA")
    assert result.lines[-1].startswith("ZEBRA")


def test_sort_keys_false_preserves_insertion_order():
    env = {"ZEBRA": "z", "ALPHA": "a"}
    result = stringify_env(env, sort_keys=False)
    assert result.lines[0].startswith("ZEBRA")


# ---------------------------------------------------------------------------
# Quoting behaviour
# ---------------------------------------------------------------------------

def test_value_with_space_is_auto_quoted():
    result = stringify_env({"MSG": "hello world"})
    assert result.lines[0] == 'MSG="hello world"'


def test_plain_value_not_quoted():
    result = stringify_env({"PORT": "8080"})
    assert result.lines[0] == "PORT=8080"


def test_quote_values_always_quotes():
    result = stringify_env({"PORT": "8080"}, quote_values=True)
    assert result.lines[0] == 'PORT="8080"'


def test_quote_values_escapes_inner_double_quotes():
    result = stringify_env({"MSG": 'say "hi"'}, quote_values=True)
    assert result.lines[0] == 'MSG="say \\"hi\\""'


# ---------------------------------------------------------------------------
# Custom separator
# ---------------------------------------------------------------------------

def test_custom_separator():
    result = stringify_env({"KEY": "val"}, separator=": ")
    assert result.lines[0] == "KEY: val"


# ---------------------------------------------------------------------------
# Format label
# ---------------------------------------------------------------------------

def test_format_label_stored():
    result = stringify_env({"A": "1"}, fmt="shell")
    assert result.format == "shell"
