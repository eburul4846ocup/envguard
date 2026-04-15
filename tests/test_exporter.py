"""Tests for envguard.exporter."""

import json
import pytest

from envguard.exporter import (
    ExportFormat,
    export_dotenv,
    export_env,
    export_json,
    export_shell,
)


SAMPLE: dict[str, str] = {
    "DB_HOST": "localhost",
    "DB_PASS": 'p@ss "word"',
    "PLAIN": "simple",
}


class TestExportShell:
    def test_produces_export_statements(self):
        out = export_shell({"FOO": "bar"})
        assert out.strip() == 'export FOO="bar"'

    def test_escapes_double_quotes(self):
        out = export_shell({"KEY": 'say "hi"'})
        assert '\\"' in out

    def test_sorted_output(self):
        out = export_shell({"Z": "1", "A": "2"})
        lines = [l for l in out.splitlines() if l]
        assert lines[0].startswith("export A=")
        assert lines[1].startswith("export Z=")

    def test_empty_dict(self):
        assert export_shell({}) == ""


class TestExportJson:
    def test_valid_json(self):
        out = export_json({"FOO": "bar"})
        data = json.loads(out)
        assert data == {"FOO": "bar"}

    def test_sorted_keys(self):
        out = export_json({"Z": "1", "A": "2"})
        data = json.loads(out)
        assert list(data.keys()) == ["A", "Z"]


class TestExportDotenv:
    def test_plain_value_no_quotes(self):
        out = export_dotenv({"KEY": "value"})
        assert out.strip() == "KEY=value"

    def test_value_with_space_is_quoted(self):
        out = export_dotenv({"KEY": "hello world"})
        assert out.strip() == 'KEY="hello world"'

    def test_value_with_hash_is_quoted(self):
        out = export_dotenv({"KEY": "val#1"})
        assert '"' in out

    def test_empty_dict(self):
        assert export_dotenv({}) == ""


class TestExportEnvDispatch:
    def test_default_is_dotenv(self):
        out = export_env({"K": "v"})
        assert "=" in out
        assert "export" not in out

    def test_shell_format(self):
        out = export_env({"K": "v"}, fmt=ExportFormat.SHELL)
        assert out.startswith("export")

    def test_json_format(self):
        out = export_env({"K": "v"}, fmt=ExportFormat.JSON)
        assert json.loads(out) == {"K": "v"}
