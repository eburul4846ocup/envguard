"""Tests for envguard.cli_group."""
import json
import os
import pytest

from envguard.cli_group import build_group_parser, _run_group


@pytest.fixture()
def env_file(tmp_path):
    return tmp_path / ".env"


def _write(path, content: str):
    path.write_text(content)
    return str(path)


def _make_args(path, prefixes=None, separator="_", min_prefix_length=2, output_format="text"):
    parser = build_group_parser()
    argv = [str(path)]
    if prefixes:
        argv += ["--prefixes"] + prefixes
    argv += ["--separator", separator]
    argv += ["--min-prefix-length", str(min_prefix_length)]
    argv += ["--format", output_format]
    return parser.parse_args(argv)


def test_group_exits_zero_for_valid_file(env_file):
    _write(env_file, "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n")
    args = _make_args(env_file)
    assert _run_group(args) == 0


def test_group_missing_file_exits_two(tmp_path):
    args = _make_args(tmp_path / "nonexistent.env")
    assert _run_group(args) == 2


def test_group_text_output_contains_group_name(env_file, capsys):
    _write(env_file, "DB_HOST=localhost\nDB_PORT=5432\n")
    args = _make_args(env_file)
    _run_group(args)
    captured = capsys.readouterr()
    assert "[DB]" in captured.out


def test_group_text_output_shows_ungrouped(env_file, capsys):
    _write(env_file, "DEBUG=true\n")
    args = _make_args(env_file)
    _run_group(args)
    captured = capsys.readouterr()
    assert "Ungrouped: 1" in captured.out


def test_group_json_output_structure(env_file, capsys):
    _write(env_file, "DB_HOST=localhost\nDEBUG=true\n")
    args = _make_args(env_file, output_format="json")
    rc = _run_group(args)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "groups" in data
    assert "ungrouped" in data
    assert "total_keys" in data
    assert data["total_keys"] == 2


def test_group_json_groups_contain_correct_keys(env_file, capsys):
    _write(env_file, "REDIS_URL=redis://\nREDIS_TTL=300\n")
    args = _make_args(env_file, output_format="json")
    _run_group(args)
    data = json.loads(capsys.readouterr().out)
    assert "REDIS" in data["groups"]
    assert "REDIS_URL" in data["groups"]["REDIS"]
    assert "REDIS_TTL" in data["groups"]["REDIS"]


def test_group_known_prefixes_limits_groups(env_file, capsys):
    _write(env_file, "DB_HOST=h\nAPP_NAME=eg\nDEBUG=true\n")
    args = _make_args(env_file, prefixes=["DB"], output_format="json")
    _run_group(args)
    data = json.loads(capsys.readouterr().out)
    assert "DB" in data["groups"]
    assert "APP" not in data["groups"]
    assert "APP_NAME" in data["ungrouped"]


def test_group_custom_separator(env_file, capsys):
    _write(env_file, "DB.HOST=localhost\nDB.PORT=5432\n")
    args = _make_args(env_file, separator=".", output_format="json")
    _run_group(args)
    data = json.loads(capsys.readouterr().out)
    assert "DB" in data["groups"]
