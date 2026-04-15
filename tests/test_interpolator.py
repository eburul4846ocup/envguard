"""Tests for envguard.interpolator."""
from __future__ import annotations

import pytest

from envguard.interpolator import interpolate, InterpolationResult


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _interp(env: dict, base: dict | None = None) -> InterpolationResult:
    return interpolate(env, base=base)


# ---------------------------------------------------------------------------
# basic behaviour
# ---------------------------------------------------------------------------

def test_no_references_returns_values_unchanged():
    result = _interp({"FOO": "bar", "BAZ": "qux"})
    assert result.resolved == {"FOO": "bar", "BAZ": "qux"}
    assert result.is_clean


def test_curly_brace_reference_expanded():
    result = _interp({"HOST": "localhost", "DSN": "postgres://${HOST}/db"})
    assert result.resolved["DSN"] == "postgres://localhost/db"


def test_bare_dollar_reference_expanded():
    result = _interp({"PORT": "5432", "ADDR": "$PORT"})
    assert result.resolved["ADDR"] == "5432"


def test_sequential_expansion_uses_earlier_keys():
    env = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
    result = _interp(env)
    assert result.resolved["B"] == "hello_world"
    assert result.resolved["C"] == "hello_world!"


def test_base_env_used_as_fallback():
    result = _interp({"GREETING": "${MSG}"}, base={"MSG": "hi"})
    assert result.resolved["GREETING"] == "hi"
    assert result.is_clean


def test_env_key_overrides_base():
    result = _interp({"X": "local", "Y": "${X}"}, base={"X": "base"})
    assert result.resolved["Y"] == "local"


# ---------------------------------------------------------------------------
# unresolved references
# ---------------------------------------------------------------------------

def test_missing_reference_leaves_token_intact():
    result = _interp({"URL": "http://${UNKNOWN_HOST}/path"})
    assert "${UNKNOWN_HOST}" in result.resolved["URL"]


def test_missing_reference_recorded():
    result = _interp({"A": "${MISSING}"})
    assert not result.is_clean
    assert "MISSING" in result.unresolved_refs


def test_multiple_unresolved_refs_all_recorded():
    result = _interp({"A": "${X}", "B": "${Y}"})
    assert set(result.unresolved_refs) == {"X", "Y"}


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_clean():
    result = _interp({"K": "v"})
    assert "successfully" in result.summary()


def test_summary_unresolved_lists_vars():
    result = _interp({"A": "${GHOST}"})
    assert "GHOST" in result.summary()


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_empty_env_returns_empty_resolved():
    result = _interp({})
    assert result.resolved == {}
    assert result.is_clean


def test_value_without_dollar_untouched():
    result = _interp({"PATH_VAL": "/usr/local/bin"})
    assert result.resolved["PATH_VAL"] == "/usr/local/bin"
