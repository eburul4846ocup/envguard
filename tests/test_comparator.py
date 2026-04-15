"""Tests for envguard.comparator module."""

import pytest
from envguard.comparator import compare_envs, ComparisonResult


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DATABASE_URL": "postgres://localhost/dev",
    "SECRET_KEY": "supersecret",
}

TARGET_IDENTICAL = dict(BASE)

TARGET_MISSING_KEY = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DATABASE_URL": "postgres://localhost/dev",
    # SECRET_KEY missing
}

TARGET_EXTRA_KEY = {
    **BASE,
    "EXTRA_VAR": "extra",
}

TARGET_VALUE_DIFF = {
    **BASE,
    "DEBUG": "true",  # changed
    "DATABASE_URL": "postgres://prod-host/prod",  # changed
}


def test_no_differences():
    result = compare_envs(BASE, TARGET_IDENTICAL)
    assert not result.has_differences
    assert result.missing_in_target == []
    assert result.missing_in_base == []
    assert result.value_mismatches == {}


def test_missing_in_target():
    result = compare_envs(BASE, TARGET_MISSING_KEY)
    assert result.has_differences
    assert "SECRET_KEY" in result.missing_in_target
    assert result.missing_in_base == []
    assert result.value_mismatches == {}


def test_extra_key_in_target():
    result = compare_envs(BASE, TARGET_EXTRA_KEY)
    assert result.has_differences
    assert "EXTRA_VAR" in result.missing_in_base
    assert result.missing_in_target == []


def test_value_mismatches():
    result = compare_envs(BASE, TARGET_VALUE_DIFF)
    assert result.has_differences
    assert "DEBUG" in result.value_mismatches
    assert "DATABASE_URL" in result.value_mismatches
    assert result.value_mismatches["DEBUG"]["base"] == "false"
    assert result.value_mismatches["DEBUG"]["target"] == "true"


def test_ignore_values_skips_mismatches():
    result = compare_envs(BASE, TARGET_VALUE_DIFF, ignore_values=True)
    assert not result.has_differences
    assert result.value_mismatches == {}


def test_summary_no_differences():
    result = compare_envs(BASE, TARGET_IDENTICAL, base_name=".env", target_name=".env.prod")
    summary = result.summary()
    assert "No differences found" in summary
    assert ".env" in summary
    assert ".env.prod" in summary


def test_summary_with_differences():
    result = compare_envs(BASE, TARGET_MISSING_KEY, base_name=".env", target_name=".env.staging")
    summary = result.summary()
    assert "SECRET_KEY" in summary
    assert "Missing in target" in summary


def test_custom_file_labels():
    result = compare_envs(BASE, TARGET_IDENTICAL, base_name="local", target_name="ci")
    assert result.base_file == "local"
    assert result.target_file == "ci"
