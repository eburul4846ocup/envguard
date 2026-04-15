"""Integration tests for the 'profile' CLI sub-command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.cli_profile import _run_profile


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def _make_args(file: Path, fmt: str = "text"):
    class _Args:
        pass

    a = _Args()
    a.file = file  # type: ignore[attr-defined]
    a.fmt = fmt  # type: ignore[attr-defined]
    return a


def test_profile_exits_zero_for_valid_file(env_file, capsys):
    _write(env_file, "APP_NAME=myapp\nDEBUG=true\n")
    code = _run_profile(_make_args(env_file))
    assert code == 0


def test_profile_missing_file_exits_two(tmp_path, capsys):
    code = _run_profile(_make_args(tmp_path / "missing.env"))
    assert code == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_profile_text_output_contains_totals(env_file, capsys):
    _write(env_file, "A=1\nB=2\n")
    _run_profile(_make_args(env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "Total keys" in out
    assert "2" in out


def test_profile_json_output_is_valid(env_file, capsys):
    _write(env_file, "SECRET_KEY=abc\nEMPTY=\nPORT=8080\n")
    code = _run_profile(_make_args(env_file, fmt="json"))
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert "summary" in data
    assert "categories" in data
    assert data["summary"]["total"] == 3


def test_profile_json_secret_detected(env_file, capsys):
    _write(env_file, "DB_PASSWORD=hunter2\n")
    _run_profile(_make_args(env_file, fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert "DB_PASSWORD" in data["categories"]["secrets"]


def test_profile_json_empty_value(env_file, capsys):
    _write(env_file, "BLANK=\n")
    _run_profile(_make_args(env_file, fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert "BLANK" in data["categories"]["empty"]
