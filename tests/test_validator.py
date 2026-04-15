"""Tests for envguard.validator module."""

import pytest
from envguard.validator import validate_env, ValidationIssue, ValidationResult


def test_valid_env_no_issues():
    env = {"HOST": "localhost", "PORT": "8080"}
    result = validate_env(env)
    assert result.is_valid
    assert result.issues == []


def test_missing_required_key():
    env = {"HOST": "localhost"}
    result = validate_env(env, required_keys=["HOST", "PORT", "SECRET_KEY"])
    assert not result.is_valid
    error_keys = {i.key for i in result.errors}
    assert "PORT" in error_keys
    assert "SECRET_KEY" in error_keys
    assert "HOST" not in error_keys


def test_empty_value_produces_warning():
    env = {"HOST": "", "PORT": "8080"}
    result = validate_env(env, allow_empty_values=False)
    assert result.is_valid  # warnings don't fail validation
    assert len(result.warnings) == 1
    assert result.warnings[0].key == "HOST"


def test_allow_empty_values_suppresses_warning():
    env = {"HOST": ""}
    result = validate_env(env, allow_empty_values=True)
    assert result.is_valid
    assert result.warnings == []


def test_value_pattern_url_valid():
    env = {"DATABASE_URL": "https://db.example.com/mydb"}
    result = validate_env(env, key_patterns={"DATABASE_URL": "url"})
    assert result.is_valid
    assert result.errors == []


def test_value_pattern_url_invalid():
    env = {"DATABASE_URL": "not-a-url"}
    result = validate_env(env, key_patterns={"DATABASE_URL": "url"})
    assert not result.is_valid
    assert result.errors[0].key == "DATABASE_URL"
    assert "url" in result.errors[0].message


def test_value_pattern_port():
    env = {"PORT": "99999", "BAD_PORT": "abc"}
    result = validate_env(env, key_patterns={"PORT": "port", "BAD_PORT": "port"})
    assert not result.is_valid
    error_keys = {i.key for i in result.errors}
    assert "BAD_PORT" in error_keys
    assert "PORT" not in error_keys


def test_value_pattern_bool():
    env = {"DEBUG": "true", "VERBOSE": "yes"}
    result = validate_env(env, key_patterns={"DEBUG": "bool", "VERBOSE": "bool"})
    error_keys = {i.key for i in result.errors}
    assert "VERBOSE" in error_keys
    assert "DEBUG" not in error_keys


def test_custom_regex_pattern():
    env = {"API_KEY": "key-abc123"}
    result = validate_env(env, key_patterns={"API_KEY": r"^key-[a-z0-9]+$"})
    assert result.is_valid


def test_pattern_skips_missing_key():
    """Pattern check should not add an error if the key is absent (required_keys handles that)."""
    env = {"HOST": "localhost"}
    result = validate_env(env, key_patterns={"PORT": "port"})
    assert result.is_valid


def test_validation_issue_str():
    issue = ValidationIssue("MY_KEY", "something wrong", severity="error")
    assert "ERROR" in str(issue)
    assert "MY_KEY" in str(issue)


def test_combined_required_and_pattern():
    env = {"PORT": "not-a-port"}
    result = validate_env(
        env,
        required_keys=["PORT", "HOST"],
        key_patterns={"PORT": "port"},
    )
    error_keys = {i.key for i in result.errors}
    assert "HOST" in error_keys   # missing
    assert "PORT" in error_keys   # bad format
