"""Integration tests for the filter CLI sub-command."""
import json
from pathlib import Path

import pytest

from envguard.cli_filter import _run_filter


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text(
        "AWS_KEY=AKIA123\nAWS_SECRET=abc\nDB_HOST=localhost\nDB_PASS=\nPORT=8080\n"
    )
    return f


class _Args:
    def __init__(self, file, prefixes=None, patterns=None, exclude_empty=False, invert=False, use_json=False):
        self.file = str(file)
        self.prefixes = prefixes or []
        self.patterns = patterns or []
        self.exclude_empty = exclude_empty
        self.invert = invert
        self.use_json = use_json


def test_filter_exits_zero_when_matches_found(env_file):
    args = _Args(env_file, prefixes=["AWS_"])
    assert _run_filter(args) == 0


def test_filter_exits_one_when_no_matches(env_file):
    args = _Args(env_file, prefixes=["NONEXISTENT_"])
    assert _run_filter(args) == 1


def test_filter_missing_file_exits_two(tmp_path):
    args = _Args(tmp_path / "missing.env")
    assert _run_filter(args) == 2


def test_filter_json_output(env_file, capsys):
    args = _Args(env_file, prefixes=["AWS_"], use_json=True)
    _run_filter(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "AWS_KEY" in data["matched"]
    assert "DB_HOST" in data["excluded"]


def test_filter_exclude_empty(env_file, capsys):
    args = _Args(env_file, prefixes=["DB_"], exclude_empty=True, use_json=True)
    _run_filter(args)
    data = json.loads(capsys.readouterr().out)
    assert "DB_HOST" in data["matched"]
    assert "DB_PASS" not in data["matched"]


def test_filter_invert(env_file, capsys):
    args = _Args(env_file, prefixes=["AWS_"], invert=True, use_json=True)
    _run_filter(args)
    data = json.loads(capsys.readouterr().out)
    assert "AWS_KEY" not in data["matched"]
    assert "DB_HOST" in data["matched"]


def test_filter_text_output_shows_summary(env_file, capsys):
    args = _Args(env_file, prefixes=["AWS_"])
    _run_filter(args)
    out = capsys.readouterr().out
    assert "Matched" in out
