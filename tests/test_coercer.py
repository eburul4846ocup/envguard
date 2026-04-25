"""Tests for envguard.coercer."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envguard.coercer import CoerceResult, coerce_env
from envguard.cli_coerce import _run_coerce


def _env(**kwargs: str):
    return dict(kwargs)


# ---------------------------------------------------------------------------
# coerce_env unit tests
# ---------------------------------------------------------------------------

class TestCoerceEnv:
    def test_plain_string_stays_str(self):
        result = coerce_env(_env(NAME="alice"))
        assert result.coerced["NAME"] == "alice"
        assert result.type_map["NAME"] == "str"

    def test_integer_value_becomes_int(self):
        result = coerce_env(_env(PORT="8080"))
        assert result.coerced["PORT"] == 8080
        assert result.type_map["PORT"] == "int"

    def test_float_value_becomes_float(self):
        result = coerce_env(_env(RATIO="3.14"))
        assert isinstance(result.coerced["RATIO"], float)
        assert result.type_map["RATIO"] == "float"

    def test_true_string_becomes_bool(self):
        for raw in ("true", "True", "TRUE", "yes", "1", "on"):
            result = coerce_env({"FLAG": raw})
            assert result.coerced["FLAG"] is True

    def test_false_string_becomes_bool(self):
        for raw in ("false", "False", "FALSE", "no", "0", "off"):
            result = coerce_env({"FLAG": raw})
            assert result.coerced["FLAG"] is False

    def test_empty_env_returns_empty_result(self):
        result = coerce_env({})
        assert result.coerced == {}
        assert result.change_count == 0
        assert not result.is_changed

    def test_change_count_only_counts_non_str(self):
        result = coerce_env(_env(A="hello", B="42", C="true"))
        assert result.change_count == 2

    def test_is_changed_false_when_all_strings(self):
        result = coerce_env(_env(A="hello", B="world"))
        assert not result.is_changed

    def test_summary_message(self):
        result = coerce_env(_env(A="hello", B="42"))
        assert "1/2" in result.summary()

    def test_to_string_contains_key_and_type(self):
        result = coerce_env(_env(PORT="9000"))
        out = result.to_string()
        assert "PORT" in out
        assert "int" in out


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class _Args:
    def __init__(self, file: str, fmt: str = "text", only_changed: bool = False):
        self.file = file
        self.fmt = fmt
        self.only_changed = only_changed


@pytest.fixture()
def env_file(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        NAME=alice
        PORT=8080
        DEBUG=true
        RATIO=1.5
    """))
    return str(p)


def test_coerce_exits_zero(env_file, capsys):
    assert _run_coerce(_Args(env_file)) == 0


def test_coerce_missing_file_exits_two(tmp_path):
    assert _run_coerce(_Args(str(tmp_path / "missing.env"))) == 2


def test_coerce_json_output_parseable(env_file, capsys):
    _run_coerce(_Args(env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["PORT"]["type"] == "int"
    assert data["DEBUG"]["type"] == "bool"


def test_coerce_only_changed_hides_strings(env_file, capsys):
    _run_coerce(_Args(env_file, only_changed=True))
    out = capsys.readouterr().out
    assert "NAME" not in out


def test_coerce_json_only_changed(env_file, capsys):
    _run_coerce(_Args(env_file, fmt="json", only_changed=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "NAME" not in data
    assert "PORT" in data
