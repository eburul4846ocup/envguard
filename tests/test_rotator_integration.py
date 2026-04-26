"""Integration tests: parse .env → rotate_env pipeline."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from envguard.parser import parse_env_file
from envguard.rotator import rotate_env


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


TODAY = date(2024, 6, 1)


def test_parse_then_rotate_no_secrets_clean(tmp_env):
    _write(tmp_env, "DEBUG=true\nHOST=localhost\nPORT=5432\n")
    env = parse_env_file(tmp_env)
    result = rotate_env(env, today=TODAY)
    assert result.is_clean
    assert result.checked == 0


def test_parse_then_rotate_secret_without_pin_is_issue(tmp_env):
    _write(tmp_env, "API_SECRET=supersecret\nDEBUG=false\n")
    env = parse_env_file(tmp_env)
    result = rotate_env(env, today=TODAY)
    assert not result.is_clean
    assert result.issue_count == 1
    assert result.issues[0].key == "API_SECRET"


def test_parse_then_rotate_with_fresh_pin_is_clean(tmp_env):
    _write(tmp_env, "DB_PASSWORD=pass123\nHOST=db\n")
    env = parse_env_file(tmp_env)
    pins = {"DB_PASSWORD": "2024-05-15"}  # 17 days old — under 90
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert result.is_clean


def test_parse_then_rotate_quoted_value_key_detected(tmp_env):
    _write(tmp_env, 'APP_TOKEN="my-token-value"\n')
    env = parse_env_file(tmp_env)
    # quotes stripped by parser; key still ends with TOKEN
    result = rotate_env(env, today=TODAY)
    assert result.issue_count == 1
    assert result.issues[0].key == "APP_TOKEN"


def test_full_pipeline_mixed_env(tmp_env):
    _write(
        tmp_env,
        "HOST=localhost\nPORT=5432\nAPI_KEY=k1\nDB_PASSWORD=p1\n",
    )
    env = parse_env_file(tmp_env)
    pins = {
        "API_KEY": "2024-05-01",      # 31 days — clean
        "DB_PASSWORD": "2023-01-01",  # stale
    }
    result = rotate_env(env, pin_dates=pins, today=TODAY)
    assert result.checked == 2
    assert result.issue_count == 1
    assert result.issues[0].key == "DB_PASSWORD"
