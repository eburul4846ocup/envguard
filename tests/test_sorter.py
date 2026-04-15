"""Tests for envguard.sorter."""
import pytest

from envguard.sorter import SortOrder, SortResult, sort_env


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# alpha
# ---------------------------------------------------------------------------

def test_alpha_order_sorts_ascending():
    env = _env(ZEBRA="1", APPLE="2", MANGO="3")
    result = sort_env(env, SortOrder.ALPHA)
    assert list(result.sorted_env.keys()) == ["APPLE", "MANGO", "ZEBRA"]


def test_alpha_desc_order_sorts_descending():
    env = _env(ZEBRA="1", APPLE="2", MANGO="3")
    result = sort_env(env, SortOrder.ALPHA_DESC)
    assert list(result.sorted_env.keys()) == ["ZEBRA", "MANGO", "APPLE"]


# ---------------------------------------------------------------------------
# length
# ---------------------------------------------------------------------------

def test_length_order_sorts_by_key_length():
    env = _env(AB="1", ABCDE="2", ABC="3")
    result = sort_env(env, SortOrder.LENGTH)
    keys = list(result.sorted_env.keys())
    assert keys[0] == "AB"
    assert keys[-1] == "ABCDE"


# ---------------------------------------------------------------------------
# group
# ---------------------------------------------------------------------------

def test_group_order_places_prefixed_keys_first():
    env = _env(DB_HOST="h", APP_NAME="n", SECRET_KEY="k", OTHER="o")
    result = sort_env(env, SortOrder.GROUP, group_prefixes=["APP_", "DB_"])
    keys = list(result.sorted_env.keys())
    assert keys.index("APP_NAME") < keys.index("OTHER")
    assert keys.index("DB_HOST") < keys.index("OTHER")


def test_group_order_respects_prefix_ordering():
    env = _env(DB_HOST="h", APP_NAME="n")
    result = sort_env(env, SortOrder.GROUP, group_prefixes=["APP_", "DB_"])
    keys = list(result.sorted_env.keys())
    assert keys.index("APP_NAME") < keys.index("DB_HOST")


def test_group_order_unknown_keys_go_to_end():
    env = _env(ZZZZZ="z", APP_X="x")
    result = sort_env(env, SortOrder.GROUP, group_prefixes=["APP_"])
    keys = list(result.sorted_env.keys())
    assert keys[0] == "APP_X"
    assert keys[-1] == "ZZZZZ"


# ---------------------------------------------------------------------------
# SortResult metadata
# ---------------------------------------------------------------------------

def test_key_count_matches_input():
    env = _env(A="1", B="2", C="3")
    result = sort_env(env)
    assert result.key_count == 3


def test_original_is_preserved_unchanged():
    env = _env(ZEBRA="1", APPLE="2")
    result = sort_env(env, SortOrder.ALPHA)
    assert list(result.original.keys()) == ["ZEBRA", "APPLE"]


def test_summary_contains_order_name():
    env = _env(A="1")
    result = sort_env(env, SortOrder.LENGTH)
    assert "length" in result.summary()


def test_empty_env_returns_empty_sorted():
    result = sort_env({})
    assert result.sorted_env == {}
    assert result.key_count == 0


def test_default_order_is_alpha():
    env = _env(Z="1", A="2")
    result = sort_env(env)
    assert result.order == SortOrder.ALPHA
    assert list(result.sorted_env.keys()) == ["A", "Z"]
