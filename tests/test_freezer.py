"""Tests for envguard.freezer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.freezer import FreezeResult, ThawResult, freeze_env, thaw_env, _checksum


@pytest.fixture()
def _env() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


def test_freeze_returns_freeze_result(_env):
    result = freeze_env(_env)
    assert isinstance(result, FreezeResult)


def test_freeze_preserves_all_keys(_env):
    result = freeze_env(_env)
    assert result.env == _env


def test_freeze_key_count(_env):
    result = freeze_env(_env)
    assert result.key_count == 3


def test_freeze_checksum_is_deterministic(_env):
    r1 = freeze_env(_env)
    r2 = freeze_env(_env)
    assert r1.checksum == r2.checksum


def test_freeze_checksum_changes_on_value_change(_env):
    r1 = freeze_env(_env)
    modified = dict(_env, DB_HOST="remotehost")
    r2 = freeze_env(modified)
    assert r1.checksum != r2.checksum


def test_freeze_summary_contains_key_count(_env):
    result = freeze_env(_env)
    assert "3" in result.summary()


def test_freeze_save_and_load(tmp_path, _env):
    dest = tmp_path / "env.freeze.json"
    result = freeze_env(_env)
    result.save(dest)
    loaded = FreezeResult.load(dest)
    assert loaded.env == result.env
    assert loaded.checksum == result.checksum


def test_thaw_no_drift(_env):
    frozen = freeze_env(_env)
    result = thaw_env(frozen, dict(_env))
    assert not result.has_drift


def test_thaw_detects_added_key(_env):
    frozen = freeze_env(_env)
    current = dict(_env, NEW_KEY="value")
    result = thaw_env(frozen, current)
    assert "NEW_KEY" in result.added
    assert result.has_drift


def test_thaw_detects_removed_key(_env):
    frozen = freeze_env(_env)
    current = {k: v for k, v in _env.items() if k != "DB_PORT"}
    result = thaw_env(frozen, current)
    assert "DB_PORT" in result.removed
    assert result.has_drift


def test_thaw_detects_changed_key(_env):
    frozen = freeze_env(_env)
    current = dict(_env, DB_HOST="newhost")
    result = thaw_env(frozen, current)
    assert "DB_HOST" in result.changed
    assert result.has_drift


def test_thaw_summary_no_drift(_env):
    frozen = freeze_env(_env)
    result = thaw_env(frozen, dict(_env))
    assert "No drift" in result.summary()


def test_thaw_summary_with_drift(_env):
    frozen = freeze_env(_env)
    current = dict(_env, EXTRA="x")
    result = thaw_env(frozen, current)
    assert "Drift" in result.summary()
