"""Unit tests for envguard.diff_reporter."""
from __future__ import annotations

import json
import pytest

from envguard.differ import EnvDiff, DiffEntry
from envguard.diff_reporter import report_diff_text, report_diff_json


def _make_diff(entries):
    return EnvDiff(source_path=".env.staging", target_path=".env.prod", entries=entries)


def test_text_no_changes():
    diff = _make_diff([
        DiffEntry("FOO", "bar", "bar", "unchanged"),
    ])
    out = report_diff_text(diff, use_color=False)
    assert "No differences found" in out
    assert "--- .env.staging" in out


def test_text_shows_added():
    diff = _make_diff([
        DiffEntry("NEW", None, "val", "added"),
    ])
    out = report_diff_text(diff, use_color=False)
    assert "+ NEW=val" in out
    assert "1 added" in out


def test_text_shows_removed():
    diff = _make_diff([
        DiffEntry("OLD", "val", None, "removed"),
    ])
    out = report_diff_text(diff, use_color=False)
    assert "- OLD=val" in out
    assert "1 removed" in out


def test_text_shows_changed():
    diff = _make_diff([
        DiffEntry("FOO", "a", "b", "changed"),
    ])
    out = report_diff_text(diff, use_color=False)
    assert "~ FOO" in out
    assert "1 changed" in out


def test_json_structure():
    diff = _make_diff([
        DiffEntry("FOO", "a", "b", "changed"),
        DiffEntry("BAR", None, "x", "added"),
    ])
    payload = json.loads(report_diff_json(diff))
    assert payload["source"] == ".env.staging"
    assert payload["target"] == ".env.prod"
    assert payload["has_changes"] is True
    assert len(payload["entries"]) == 2
    keys = {e["key"] for e in payload["entries"]}
    assert keys == {"FOO", "BAR"}


def test_json_no_changes():
    diff = _make_diff([
        DiffEntry("FOO", "bar", "bar", "unchanged"),
    ])
    payload = json.loads(report_diff_json(diff))
    assert payload["has_changes"] is False
