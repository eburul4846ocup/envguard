"""Tests for envguard.cli_freeze."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.cli_freeze import _run_freeze, _run_thaw


@pytest.fixture()
def env_file(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n")
    return p


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_freeze_exits_zero(env_file, tmp_path):
    dest = tmp_path / "out.freeze.json"
    args = _Args(env_file=env_file, output=dest)
    assert _run_freeze(args) == 0
    assert dest.exists()


def test_freeze_creates_valid_json(env_file, tmp_path):
    dest = tmp_path / "out.freeze.json"
    args = _Args(env_file=env_file, output=dest)
    _run_freeze(args)
    payload = json.loads(dest.read_text())
    assert "env" in payload
    assert "checksum" in payload
    assert payload["env"]["DB_HOST"] == "localhost"


def test_freeze_missing_file_exits_two(tmp_path):
    args = _Args(env_file=tmp_path / "missing.env", output=None)
    assert _run_freeze(args) == 2


def test_freeze_default_output_path(env_file):
    args = _Args(env_file=env_file, output=None)
    _run_freeze(args)
    expected = env_file.with_suffix(".freeze.json")
    assert expected.exists()


def test_thaw_no_drift_exits_zero(env_file, tmp_path):
    freeze_path = tmp_path / "snap.freeze.json"
    _run_freeze(_Args(env_file=env_file, output=freeze_path))
    args = _Args(freeze_file=freeze_path, env_file=env_file, as_json=False)
    assert _run_thaw(args) == 0


def test_thaw_drift_exits_one(env_file, tmp_path):
    freeze_path = tmp_path / "snap.freeze.json"
    _run_freeze(_Args(env_file=env_file, output=freeze_path))
    env_file.write_text("DB_HOST=changed\nDB_PORT=5432\nSECRET_KEY=abc\n")
    args = _Args(freeze_file=freeze_path, env_file=env_file, as_json=False)
    assert _run_thaw(args) == 1


def test_thaw_json_output(env_file, tmp_path, capsys):
    freeze_path = tmp_path / "snap.freeze.json"
    _run_freeze(_Args(env_file=env_file, output=freeze_path))
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\nNEW=val\n")
    args = _Args(freeze_file=freeze_path, env_file=env_file, as_json=True)
    _run_thaw(args)
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["has_drift"] is True
    assert "NEW" in data["added"]


def test_thaw_missing_freeze_file_exits_two(env_file, tmp_path):
    args = _Args(freeze_file=tmp_path / "no.json", env_file=env_file, as_json=False)
    assert _run_thaw(args) == 2


def test_thaw_missing_env_file_exits_two(tmp_path):
    freeze_path = tmp_path / "snap.freeze.json"
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    _run_freeze(_Args(env_file=env, output=freeze_path))
    args = _Args(freeze_file=freeze_path, env_file=tmp_path / "gone.env", as_json=False)
    assert _run_thaw(args) == 2
