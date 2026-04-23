"""Tests for envguard.cascader."""
from __future__ import annotations

import pytest

from envguard.cascader import CascadeResult, cascade_envs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# cascade_envs
# ---------------------------------------------------------------------------

def test_empty_layers_returns_empty():
    result = cascade_envs([])
    assert result.merged == {}
    assert result.provenance == {}
    assert result.key_count == 0


def test_single_layer_passthrough():
    env = _env(FOO="bar", BAZ="qux")
    result = cascade_envs([env])
    assert result.merged == env
    assert result.overridden_keys == []


def test_later_layer_overrides_earlier():
    base = _env(FOO="base", SHARED="base")
    overlay = _env(SHARED="overlay", NEW="value")
    result = cascade_envs([base, overlay])
    assert result.merged["SHARED"] == "overlay"
    assert result.merged["FOO"] == "base"
    assert result.merged["NEW"] == "value"


def test_overridden_keys_lists_changed_keys():
    base = _env(A="1", B="2")
    overlay = _env(A="99")
    result = cascade_envs([base, overlay])
    assert result.overridden_keys == ["A"]


def test_no_override_when_layers_disjoint():
    base = _env(FOO="1")
    overlay = _env(BAR="2")
    result = cascade_envs([base, overlay])
    assert result.overridden_keys == []
    assert result.key_count == 2


def test_three_layers_last_wins():
    l1 = _env(X="1")
    l2 = _env(X="2")
    l3 = _env(X="3")
    result = cascade_envs([l1, l2, l3])
    assert result.merged["X"] == "3"


def test_provenance_records_all_values():
    l1 = _env(X="a")
    l2 = _env(X="b")
    result = cascade_envs([l1, l2])
    chain = result.provenance["X"]
    assert chain == [(0, "a"), (1, "b")]


def test_provenance_single_occurrence():
    result = cascade_envs([_env(ONLY="here")])
    assert result.provenance["ONLY"] == [(0, "here")]


def test_summary_format():
    base = _env(A="1", B="2")
    overlay = _env(A="99", C="3")
    result = cascade_envs([base, overlay])
    s = result.summary()
    assert "3 key(s) in final env" in s
    assert "1 key(s) overridden" in s


def test_key_count_property():
    result = cascade_envs([_env(A="1"), _env(B="2"), _env(C="3")])
    assert result.key_count == 3
