"""Tests for envguard.injector."""
import pytest

from envguard.injector import InjectResult, inject_env


def _src(**kw: str) -> dict:
    return dict(kw)


# ---------------------------------------------------------------------------
# inject_env — basic behaviour
# ---------------------------------------------------------------------------

def test_empty_source_returns_empty_result():
    result = inject_env({}, target={"A": "1"})
    assert result.inject_count == 0
    assert result.skip_count == 0


def test_new_keys_are_injected():
    result = inject_env({"FOO": "bar", "BAZ": "qux"}, target={})
    assert result.injected == {"FOO": "bar", "BAZ": "qux"}
    assert result.skip_count == 0


def test_existing_key_without_override_is_skipped():
    result = inject_env({"FOO": "new"}, target={"FOO": "old"})
    assert result.skip_count == 1
    assert "FOO" in result.skipped
    assert result.inject_count == 0


def test_existing_key_with_override_is_overridden():
    result = inject_env({"FOO": "new"}, target={"FOO": "old"}, override=True)
    assert result.override_count == 1
    assert result.overridden["FOO"] == "new"
    assert result.inject_count == 0


def test_keys_filter_limits_injection():
    result = inject_env({"A": "1", "B": "2", "C": "3"}, keys=["A", "C"])
    assert set(result.injected.keys()) == {"A", "C"}
    assert "B" not in result.injected


def test_keys_filter_with_missing_key_ignored():
    result = inject_env({"A": "1"}, keys=["A", "MISSING"])
    assert result.inject_count == 1


# ---------------------------------------------------------------------------
# InjectResult helpers
# ---------------------------------------------------------------------------

def test_is_changed_true_when_injected():
    result = inject_env({"X": "1"})
    assert result.is_changed is True


def test_is_changed_false_when_all_skipped():
    result = inject_env({"X": "1"}, target={"X": "old"})
    assert result.is_changed is False


def test_summary_includes_injected_count():
    result = inject_env({"A": "1", "B": "2"})
    assert "injected=2" in result.summary()


def test_summary_includes_skipped_when_nonzero():
    result = inject_env({"A": "1"}, target={"A": "old"})
    assert "skipped=1" in result.summary()


def test_summary_omits_skipped_when_zero():
    result = inject_env({"A": "1"})
    assert "skipped" not in result.summary()


# ---------------------------------------------------------------------------
# merged_env
# ---------------------------------------------------------------------------

def test_merged_env_combines_base_and_injected():
    result = inject_env({"NEW": "val"}, target={"OLD": "existing"})
    merged = result.merged_env(base={"OLD": "existing"})
    assert merged["OLD"] == "existing"
    assert merged["NEW"] == "val"


def test_merged_env_applies_overrides():
    result = inject_env({"K": "v2"}, target={"K": "v1"}, override=True)
    merged = result.merged_env(base={"K": "v1"})
    assert merged["K"] == "v2"


def test_merged_env_default_base_is_empty():
    result = inject_env({"A": "1"})
    assert result.merged_env() == {"A": "1"}
