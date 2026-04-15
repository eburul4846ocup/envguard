"""Integration tests for the `envguard redact` CLI sub-command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.cli_redact import build_redact_parser, _run_redact


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def _make_args(file: Path, **kwargs):
    import argparse

    defaults = {
        "file": str(file),
        "mask": "***",
        "extra_keys": [],
        "format": "dotenv",
        "summary": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_redact_exits_zero_for_valid_file(env_file, capsys):
    _write(env_file, "APP_NAME=myapp\nDB_PASSWORD=secret\n")
    rc = _run_redact(_make_args(env_file))
    assert rc == 0


def test_redact_masks_secret_values(env_file, capsys):
    _write(env_file, "DB_PASSWORD=hunter2\nAPP_NAME=myapp\n")
    _run_redact(_make_args(env_file))
    out = capsys.readouterr().out
    assert "hunter2" not in out
    assert "***" in out
    assert "myapp" in out


def test_redact_custom_mask(env_file, capsys):
    _write(env_file, "API_KEY=abc123\n")
    _run_redact(_make_args(env_file, mask="<REDACTED>"))
    out = capsys.readouterr().out
    assert "<REDACTED>" in out
    assert "abc123" not in out


def test_redact_json_format(env_file, capsys):
    _write(env_file, "DB_PASSWORD=secret\nPORT=8080\n")
    _run_redact(_make_args(env_file, format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["DB_PASSWORD"] == "***"
    assert data["PORT"] == "8080"


def test_redact_extra_keys(env_file, capsys):
    _write(env_file, "PLAIN=value\nSAFE=ok\n")
    _run_redact(_make_args(env_file, extra_keys=["PLAIN"]))
    out = capsys.readouterr().out
    assert "value" not in out
    assert "***" in out


def test_redact_summary_written_to_stderr(env_file, capsys):
    _write(env_file, "DB_PASSWORD=s3cr3t\nAPP=x\n")
    _run_redact(_make_args(env_file, summary=True))
    err = capsys.readouterr().err
    assert "Redacted" in err


def test_redact_missing_file_exits_two(tmp_path, capsys):
    missing = tmp_path / "nonexistent.env"
    rc = _run_redact(_make_args(missing))
    assert rc == 2
    assert "not found" in capsys.readouterr().err
