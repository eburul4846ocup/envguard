"""Tests for envguard.pinner."""
import json
import pytest
from pathlib import Path
from envguard.pinner import pin_env, save_pin, load_pin, detect_drift


@pytest.fixture
def base_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


def test_pin_env_returns_pin_result(base_env):
    result = pin_env(base_env, source=".env")
    assert result.source == ".env"
    assert result.pinned == dict(sorted(base_env.items()))
    assert len(result.checksum) == 64


def test_pin_env_key_count(base_env):
    result = pin_env(base_env, source=".env")
    assert result.key_count() == 3


def test_pin_env_summary(base_env):
    result = pin_env(base_env, source=".env")
    assert "3 keys" in result.summary()
    assert ".env" in result.summary()


def test_save_and_load_pin(tmp_path, base_env):
    lock = tmp_path / "env.lock"
    result = pin_env(base_env, source=".env")
    save_pin(result, lock)
    loaded = load_pin(lock)
    assert loaded.pinned == result.pinned
    assert loaded.checksum == result.checksum
    assert loaded.source == result.source


def test_save_pin_creates_valid_json(tmp_path, base_env):
    lock = tmp_path / "env.lock"
    save_pin(pin_env(base_env, source=".env"), lock)
    data = json.loads(lock.read_text())
    assert "pinned" in data and "checksum" in data and "source" in data


def test_detect_drift_no_changes(base_env):
    pin = pin_env(base_env, source=".env")
    drift = detect_drift(pin, base_env)
    assert not drift.has_drift()
    assert drift.summary() == "No drift detected"


def test_detect_drift_value_changed(base_env):
    pin = pin_env(base_env, source=".env")
    current = {**base_env, "DB_HOST": "prod-db"}
    drift = detect_drift(pin, current)
    assert drift.has_drift()
    assert "DB_HOST" in drift.drifted
    assert drift.drifted["DB_HOST"] == ("localhost", "prod-db")


def test_detect_drift_added_key(base_env):
    pin = pin_env(base_env, source=".env")
    current = {**base_env, "NEW_KEY": "new"}
    drift = detect_drift(pin, current)
    assert "NEW_KEY" in drift.added


def test_detect_drift_removed_key(base_env):
    pin = pin_env(base_env, source=".env")
    current = {k: v for k, v in base_env.items() if k != "DB_PORT"}
    drift = detect_drift(pin, current)
    assert "DB_PORT" in drift.removed


def test_drift_summary_shows_all_categories(base_env):
    pin = pin_env(base_env, source=".env")
    current = {"DB_HOST": "prod", "NEW": "val"}  # changed, removed DB_PORT+SECRET_KEY, added NEW
    drift = detect_drift(pin, current)
    summary = drift.summary()
    assert "changed" in summary
    assert "added" in summary
    assert "removed" in summary
