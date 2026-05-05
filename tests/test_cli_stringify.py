"""Tests for envguard.cli_stringify._run_stringify."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.cli_stringify import _run_stringify


@pytest.fixture()
def env_file(tmp_path: Path):
    return tmp_path / ".env"


def _write(p: Path, text: str) -> Path:
    p.write_text(text)
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "",
        "quote_values": False,
        "no_sort": False,
        "separator": "=",
        "fmt": "dotenv",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------

def test_stringify_exits_zero_for_valid_file(env_file, capsys):
    _write(env_file, "PORT=8080\nDEBUG=true\n")
    code = _run_stringify(_args(file=str(env_file)))
    assert code == 0


def test_stringify_missing_file_exits_two(tmp_path, capsys):
    code = _run_stringify(_args(file=str(tmp_path / "missing.env")))
    assert code == 2


def test_stringify_output_contains_keys(env_file, capsys):
    _write(env_file, "ALPHA=1\nBETA=2\n")
    _run_stringify(_args(file=str(env_file)))
    out = capsys.readouterr().out
    assert "ALPHA=1" in out
    assert "BETA=2" in out


def test_stringify_quote_values_flag(env_file, capsys):
    _write(env_file, "PORT=8080\n")
    _run_stringify(_args(file=str(env_file), quote_values=True))
    out = capsys.readouterr().out
    assert 'PORT="8080"' in out


def test_stringify_no_sort_preserves_order(env_file, capsys):
    _write(env_file, "ZEBRA=z\nALPHA=a\n")
    _run_stringify(_args(file=str(env_file), no_sort=True))
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if l.strip()]
    assert lines[0].startswith("ZEBRA")


def test_stringify_custom_separator(env_file, capsys):
    _write(env_file, "KEY=value\n")
    _run_stringify(_args(file=str(env_file), separator=": "))
    out = capsys.readouterr().out
    assert "KEY: value" in out


def test_stringify_summary_in_stderr(env_file, capsys):
    _write(env_file, "A=1\nB=2\n")
    _run_stringify(_args(file=str(env_file)))
    err = capsys.readouterr().err
    assert "2" in err
