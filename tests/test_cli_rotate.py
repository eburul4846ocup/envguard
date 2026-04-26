"""CLI tests for envguard rotate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.cli_rotate import _run_rotate, build_rotate_parser


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


class _Args:
    def __init__(self, env_file, pins=None, max_age=90, json_output=False):
        self.env_file = str(env_file)
        self.pins = str(pins) if pins else None
        self.max_age = max_age
        self.json_output = json_output


def test_rotate_clean_exits_zero(env_dir):
    env = _write(env_dir / ".env", "DEBUG=true\nHOST=localhost\n")
    args = _Args(env)
    assert _run_rotate(args) == 0


def test_rotate_missing_file_exits_two(env_dir):
    args = _Args(env_dir / "missing.env")
    assert _run_rotate(args) == 2


def test_rotate_missing_pins_file_exits_two(env_dir):
    env = _write(env_dir / ".env", "API_KEY=abc\n")
    args = _Args(env, pins=env_dir / "no_pins.json")
    assert _run_rotate(args) == 2


def test_rotate_secret_no_pins_exits_one(env_dir):
    env = _write(env_dir / ".env", "API_SECRET=value\n")
    args = _Args(env)
    assert _run_rotate(args) == 1


def test_rotate_fresh_pin_exits_zero(env_dir):
    env = _write(env_dir / ".env", "API_KEY=abc\n")
    pins = env_dir / "pins.json"
    pins.write_text(json.dumps({"API_KEY": "2099-01-01"}))
    args = _Args(env, pins=pins, max_age=90)
    assert _run_rotate(args) == 0


def test_rotate_stale_pin_exits_one(env_dir):
    env = _write(env_dir / ".env", "DB_PASSWORD=secret\n")
    pins = env_dir / "pins.json"
    pins.write_text(json.dumps({"DB_PASSWORD": "2000-01-01"}))
    args = _Args(env, pins=pins, max_age=90)
    assert _run_rotate(args) == 1


def test_rotate_json_output_is_valid_json(env_dir, capsys):
    env = _write(env_dir / ".env", "API_TOKEN=x\n")
    args = _Args(env, json_output=True)
    _run_rotate(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "is_clean" in data
    assert "issues" in data


def test_rotate_json_output_contains_issue_details(env_dir, capsys):
    env = _write(env_dir / ".env", "API_TOKEN=x\n")
    pins = env_dir / "pins.json"
    pins.write_text(json.dumps({"API_TOKEN": "2000-06-01"}))
    args = _Args(env, pins=pins, max_age=90, json_output=True)
    _run_rotate(args)
    data = json.loads(capsys.readouterr().out)
    assert data["issue_count"] == 1
    assert data["issues"][0]["key"] == "API_TOKEN"


def test_build_rotate_parser_returns_parser():
    p = build_rotate_parser()
    args = p.parse_args(["myfile.env", "--max-age", "30"])
    assert args.max_age == 30
