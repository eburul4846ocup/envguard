"""Tests for envguard.reporter."""

from __future__ import annotations

import io
import json

import pytest

from envguard.comparator import ComparisonResult
from envguard.reporter import OutputFormat, report_json, report_text


def _result(
    missing=None,
    extra=None,
    mismatched=None,
) -> ComparisonResult:
    return ComparisonResult(
        missing_keys=set(missing or []),
        extra_keys=set(extra or []),
        mismatched_values=dict(mismatched or {}),
    )


# ---------------------------------------------------------------------------
# report_text
# ---------------------------------------------------------------------------

def test_text_no_differences():
    out = io.StringIO()
    report_text(_result(), out=out, use_color=False)
    assert "No differences found" in out.getvalue()


def test_text_missing_keys():
    out = io.StringIO()
    report_text(_result(missing=["DB_HOST", "API_KEY"]), out=out, use_color=False)
    text = out.getvalue()
    assert "Missing keys in target" in text
    assert "DB_HOST" in text
    assert "API_KEY" in text


def test_text_extra_keys():
    out = io.StringIO()
    report_text(_result(extra=["EXTRA_VAR"]), out=out, use_color=False)
    text = out.getvalue()
    assert "Extra keys in target" in text
    assert "EXTRA_VAR" in text


def test_text_mismatched_values():
    out = io.StringIO()
    report_text(
        _result(mismatched={"PORT": ("8080", "9090")}),
        out=out,
        use_color=False,
    )
    text = out.getvalue()
    assert "Value mismatches" in text
    assert "PORT" in text
    assert "8080" in text
    assert "9090" in text


def test_text_includes_summary():
    out = io.StringIO()
    report_text(
        _result(missing=["X"], extra=["Y"], mismatched={"Z": ("a", "b")}),
        out=out,
        use_color=False,
    )
    text = out.getvalue()
    # summary line produced by ComparisonResult.summary()
    assert "missing" in text.lower() or "mismatch" in text.lower()


# ---------------------------------------------------------------------------
# report_json
# ---------------------------------------------------------------------------

def test_json_no_differences():
    out = io.StringIO()
    report_json(_result(), out=out)
    data = json.loads(out.getvalue())
    assert data["has_differences"] is False
    assert data["missing_keys"] == []
    assert data["extra_keys"] == []
    assert data["mismatched_values"] == {}


def test_json_full_diff():
    out = io.StringIO()
    report_json(
        _result(missing=["A"], extra=["B"], mismatched={"C": ("old", "new")}),
        source_name=".env.prod",
        target_name=".env.staging",
        out=out,
    )
    data = json.loads(out.getvalue())
    assert data["has_differences"] is True
    assert "A" in data["missing_keys"]
    assert "B" in data["extra_keys"]
    assert data["mismatched_values"]["C"] == {"source": "old", "target": "new"}
    assert data["source"] == ".env.prod"
    assert data["target"] == ".env.staging"


def test_output_format_enum():
    assert OutputFormat.TEXT == "text"
    assert OutputFormat.JSON == "json"
