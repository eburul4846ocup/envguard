"""Unit tests for envguard.differ."""
from __future__ import annotations

import os
import pytest

from envguard.differ import diff_env_files, EnvDiff, DiffEntry


@pytest.fixture()
def tmp_env(tmp_path):
    """Return a helper that writes a .env file and returns its path."""
    def _write(name: str, content: str) -> str:
        p = tmp_path / name
        p.write_text(content)
        return str(p)
    return _write


def test_no_changes(tmp_env):
    src = tmp_env("a.env", "FOO=bar\nBAZ=qux\n")
    tgt = tmp_env("b.env", "FOO=bar\nBAZ=qux\n")
    diff = diff_env_files(src, tgt)
    assert not diff.has_changes
    assert diff.added == []
    assert diff.removed == []
    assert diff.changed == []


def test_added_key(tmp_env):
    src = tmp_env("a.env", "FOO=bar\n")
    tgt = tmp_env("b.env", "FOO=bar\nNEW=value\n")
    diff = diff_env_files(src, tgt)
    assert diff.has_changes
    assert len(diff.added) == 1
    assert diff.added[0].key == "NEW"
    assert diff.added[0].target_value == "value"
    assert diff.added[0].source_value is None


def test_removed_key(tmp_env):
    src = tmp_env("a.env", "FOO=bar\nGONE=old\n")
    tgt = tmp_env("b.env", "FOO=bar\n")
    diff = diff_env_files(src, tgt)
    assert len(diff.removed) == 1
    assert diff.removed[0].key == "GONE"
    assert diff.removed[0].source_value == "old"


def test_changed_value(tmp_env):
    src = tmp_env("a.env", "FOO=old\n")
    tgt = tmp_env("b.env", "FOO=new\n")
    diff = diff_env_files(src, tgt)
    assert len(diff.changed) == 1
    entry = diff.changed[0]
    assert entry.key == "FOO"
    assert entry.source_value == "old"
    assert entry.target_value == "new"
    assert entry.status == "changed"


def test_ignore_values_no_changed(tmp_env):
    src = tmp_env("a.env", "FOO=old\n")
    tgt = tmp_env("b.env", "FOO=new\n")
    diff = diff_env_files(src, tgt, ignore_values=True)
    assert not diff.has_changes
    assert diff.changed == []


def test_diff_entry_str_representations():
    assert str(DiffEntry("K", "v", None, "removed")).startswith("-")
    assert str(DiffEntry("K", None, "v", "added")).startswith("+")
    assert str(DiffEntry("K", "a", "b", "changed")).startswith("~")
    assert str(DiffEntry("K", "v", "v", "unchanged")).startswith(" ")


def test_paths_stored(tmp_env):
    src = tmp_env("a.env", "")
    tgt = tmp_env("b.env", "")
    diff = diff_env_files(src, tgt)
    assert diff.source_path == src
    assert diff.target_path == tgt
