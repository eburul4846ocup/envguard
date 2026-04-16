"""Tests for envguard.cli_scan."""
import json
import pytest
from pathlib import Path
from types import SimpleNamespace
from envguard.cli_scan import _run_scan


@pytest.fixture
def env_file(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, content: str):
    path.write_text(content)


def _args(file, fmt="text"):
    return SimpleNamespace(file=str(file), fmt=fmt)


def test_scan_clean_file_exits_zero(env_file):
    _write(env_file, "APP_NAME=myapp\nDEBUG=true\n")
    assert _run_scan(_args(env_file)) == 0


def test_scan_secret_exits_one(env_file):
    _write(env_file, "AWS_KEY=AKIAIOSFODNN7EXAMPLE\n")
    assert _run_scan(_args(env_file)) == 1


def test_scan_missing_file_exits_two(tmp_path):
    assert _run_scan(_args(tmp_path / "missing.env")) == 2


def test_scan_json_output_clean(env_file, capsys):
    _write(env_file, "PORT=8080\n")
    code = _run_scan(_args(env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["clean"] is True
    assert data["hit_count"] == 0
    assert code == 0


def test_scan_json_output_with_hits(env_file, capsys):
    _write(env_file, "GH_TOKEN=ghp_" + "A" * 36 + "\n")
    code = _run_scan(_args(env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["clean"] is False
    assert data["hit_count"] == 1
    assert data["hits"][0]["key"] == "GH_TOKEN"
    assert code == 1


def test_scan_text_output_summary(env_file, capsys):
    _write(env_file, "APP=ok\n")
    _run_scan(_args(env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "No hardcoded" in out
