"""Tests for envguard.cli_deprecate."""
import json
import pytest
from pathlib import Path
from envguard.cli_deprecate import _run_deprecate


@pytest.fixture()
def env_file(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, content: str):
    path.write_text(content)


class _Args:
    def __init__(self, env_file, map=None, no_replacement=None, json_out=False):
        self.env_file = str(env_file)
        self.map = map or []
        self.no_replacement = no_replacement or []
        self.json_out = json_out


def test_clean_env_exits_zero(env_file):
    _write(env_file, "HOST=localhost\nPORT=5432\n")
    assert _run_deprecate(_Args(env_file)) == 0


def test_deprecated_key_exits_one(env_file):
    _write(env_file, "OLD_DB_URL=postgres://localhost/db\n")
    assert _run_deprecate(_Args(env_file, map=["OLD_DB_URL:DATABASE_URL"])) == 1


def test_no_replacement_exits_one(env_file):
    _write(env_file, "LEGACY_FLAG=1\n")
    assert _run_deprecate(_Args(env_file, no_replacement=["LEGACY_FLAG"])) == 1


def test_missing_file_exits_two(tmp_path):
    args = _Args(tmp_path / "missing.env")
    assert _run_deprecate(args) == 2


def test_json_output_clean(env_file, capsys):
    _write(env_file, "HOST=localhost\n")
    code = _run_deprecate(_Args(env_file, json_out=True))
    out = json.loads(capsys.readouterr().out)
    assert out["is_clean"] is True
    assert out["issues"] == []
    assert code == 0


def test_json_output_with_issue(env_file, capsys):
    _write(env_file, "OLD=value\n")
    _run_deprecate(_Args(env_file, map=["OLD:NEW"], json_out=True))
    out = json.loads(capsys.readouterr().out)
    assert out["is_clean"] is False
    assert out["issues"][0]["key"] == "OLD"
    assert out["issues"][0]["replacement"] == "NEW"
