"""Tests for envguard.snapshot."""
import json
import time
from pathlib import Path

import pytest

from envguard.snapshot import Snapshot, capture, load_snapshot, save_snapshot


ENV_A = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "old"}
ENV_B = {"DB_HOST": "prod.host", "DB_PORT": "5432", "API_KEY": "xyz"}


def _snap(env: dict, source: str = "test", label=None) -> Snapshot:
    return capture(env, source=source, label=label)


class TestSnapshotDiff:
    def test_keys_added(self):
        prev = _snap(ENV_A)
        curr = _snap(ENV_B)
        assert curr.keys_added_since(prev) == ["API_KEY"]

    def test_keys_removed(self):
        prev = _snap(ENV_A)
        curr = _snap(ENV_B)
        assert curr.keys_removed_since(prev) == ["SECRET"]

    def test_keys_changed(self):
        prev = _snap(ENV_A)
        curr = _snap(ENV_B)
        assert curr.keys_changed_since(prev) == ["DB_HOST"]

    def test_no_changes(self):
        snap = _snap(ENV_A)
        assert not snap.has_changes_since(snap)

    def test_has_changes(self):
        prev = _snap(ENV_A)
        curr = _snap(ENV_B)
        assert curr.has_changes_since(prev)

    def test_identical_envs_no_changes(self):
        a = _snap({"K": "v"})
        b = _snap({"K": "v"})
        assert not b.has_changes_since(a)


class TestCapture:
    def test_label_stored(self):
        s = capture({"X": "1"}, source=".env", label="pre-deploy")
        assert s.label == "pre-deploy"

    def test_captured_at_is_recent(self):
        before = time.time()
        s = capture({}, source=".env")
        assert s.captured_at >= before

    def test_env_is_copy(self):
        env = {"A": "1"}
        s = capture(env, source=".env")
        env["A"] = "mutated"
        assert s.env["A"] == "1"


class TestPersistence:
    def test_round_trip(self, tmp_path: Path):
        original = capture({"FOO": "bar", "BAZ": "qux"}, source=".env", label="v1")
        p = tmp_path / "snap.json"
        save_snapshot(original, p)
        loaded = load_snapshot(p)
        assert loaded.env == original.env
        assert loaded.label == "v1"
        assert loaded.source == ".env"
        assert loaded.captured_at == pytest.approx(original.captured_at)

    def test_saved_file_is_valid_json(self, tmp_path: Path):
        snap = capture({"K": "v"}, source=".env")
        p = tmp_path / "snap.json"
        save_snapshot(snap, p)
        data = json.loads(p.read_text())
        assert "env" in data
        assert data["env"] == {"K": "v"}
