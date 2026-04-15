"""Integration tests for the `envguard diff` CLI sub-command."""
from __future__ import annotations

import json
import pytest

from envguard.cli import build_parser, main


@pytest.fixture()
def env_file(tmp_path):
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def test_diff_no_changes_exits_zero(env_file, capsys):
    src = env_file("a.env", "FOO=bar\nBAZ=qux\n")
    tgt = env_file("b.env", "FOO=bar\nBAZ=qux\n")
    rc = main(["diff", src, tgt])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No differences" in out


def test_diff_with_changes_exits_one(env_file, capsys):
    src = env_file("a.env", "FOO=bar\nGONE=old\n")
    tgt = env_file("b.env", "FOO=changed\n")
    rc = main(["diff", src, tgt])
    assert rc == 1


def test_diff_json_output(env_file, capsys):
    src = env_file("a.env", "FOO=bar\n")
    tgt = env_file("b.env", "FOO=bar\nNEW=hello\n")
    rc = main(["diff", "--format", "json", src, tgt])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["has_changes"] is True
    statuses = {e["key"]: e["status"] for e in payload["entries"]}
    assert statuses["NEW"] == "added"
    assert rc == 1


def test_diff_ignore_values(env_file, capsys):
    src = env_file("a.env", "FOO=old\n")
    tgt = env_file("b.env", "FOO=new\n")
    rc = main(["diff", "--ignore-values", src, tgt])
    assert rc == 0


def test_diff_missing_file_exits_two(env_file, capsys):
    src = env_file("a.env", "FOO=bar\n")
    rc = main(["diff", src, "/nonexistent/.env"])
    assert rc == 2
