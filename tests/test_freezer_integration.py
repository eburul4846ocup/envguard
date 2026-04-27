"""Integration tests: parse → freeze → mutate → thaw pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from envguard.freezer import freeze_env, thaw_env
from envguard.parser import parse_env_file


@pytest.fixture()
def tmp_env(tmp_path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        'APP_ENV=production\nDB_URL=postgres://localhost/db\nSECRET_KEY="s3cr3t"\n'
    )
    return p


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_parse_then_freeze_key_count(tmp_env):
    env = parse_env_file(tmp_env)
    result = freeze_env(env)
    assert result.key_count == 3


def test_freeze_save_load_roundtrip(tmp_env, tmp_path):
    from envguard.freezer import FreezeResult

    env = parse_env_file(tmp_env)
    frozen = freeze_env(env)
    dest = tmp_path / "state.freeze.json"
    frozen.save(dest)
    loaded = FreezeResult.load(dest)
    assert loaded.checksum == frozen.checksum
    assert loaded.env == frozen.env


def test_no_drift_after_identical_parse(tmp_env):
    env = parse_env_file(tmp_env)
    frozen = freeze_env(env)
    current = parse_env_file(tmp_env)
    result = thaw_env(frozen, current)
    assert not result.has_drift


def test_drift_detected_after_value_change(tmp_env):
    env = parse_env_file(tmp_env)
    frozen = freeze_env(env)
    _write(tmp_env, 'APP_ENV=staging\nDB_URL=postgres://localhost/db\nSECRET_KEY="s3cr3t"\n')
    current = parse_env_file(tmp_env)
    result = thaw_env(frozen, current)
    assert result.has_drift
    assert "APP_ENV" in result.changed


def test_drift_detected_after_key_removal(tmp_env):
    env = parse_env_file(tmp_env)
    frozen = freeze_env(env)
    _write(tmp_env, "APP_ENV=production\nDB_URL=postgres://localhost/db\n")
    current = parse_env_file(tmp_env)
    result = thaw_env(frozen, current)
    assert "SECRET_KEY" in result.removed
