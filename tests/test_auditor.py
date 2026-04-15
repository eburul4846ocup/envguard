"""Tests for envguard.auditor."""
import pytest

from envguard.auditor import AuditSeverity, audit_env


def test_clean_env_no_issues():
    env = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "true"}
    result = audit_env(env)
    assert result.is_clean
    assert result.issues == []


def test_empty_secret_value_is_warning():
    result = audit_env({"DB_PASSWORD": ""})
    assert not result.is_clean
    assert len(result.warnings) == 1
    assert result.warnings[0].key == "DB_PASSWORD"
    assert result.errors == []


def test_placeholder_value_is_warning():
    result = audit_env({"API_KEY": "changeme"})
    assert len(result.warnings) == 1
    assert "placeholder" in result.warnings[0].message


def test_real_secret_value_is_error():
    result = audit_env({"AUTH_TOKEN": "s3cr3t-abc123"})
    assert len(result.errors) == 1
    assert result.errors[0].key == "AUTH_TOKEN"
    assert result.warnings == []


def test_non_secret_key_ignored():
    result = audit_env({"LOG_LEVEL": "debug", "HOST": "localhost"})
    assert result.is_clean


def test_multiple_secret_keys():
    env = {
        "DB_PASSWORD": "hunter2",
        "STRIPE_SECRET_KEY": "sk_live_abc",
        "APP_NAME": "envguard",
    }
    result = audit_env(env)
    assert len(result.errors) == 2
    keys = {i.key for i in result.errors}
    assert keys == {"DB_PASSWORD", "STRIPE_SECRET_KEY"}


def test_flag_placeholders_false_suppresses_placeholder_warning():
    result = audit_env({"API_KEY": "<your-api-key>"}, flag_placeholders=False)
    # Value is non-empty and not a placeholder check → treated as real secret
    assert len(result.errors) == 1


def test_placeholder_variants():
    placeholders = ["TODO", "FIXME", "your_token", "${MY_SECRET}", "xxxxx"]
    for ph in placeholders:
        result = audit_env({"PRIVATE_KEY": ph})
        assert len(result.warnings) == 1, f"expected warning for placeholder {ph!r}"


def test_str_representation():
    result = audit_env({"DB_PASSWORD": "realpass"})
    issue_str = str(result.errors[0])
    assert "ERROR" in issue_str
    assert "DB_PASSWORD" in issue_str


def test_case_insensitive_key_matching():
    # Keys like 'dbpassword' (all lowercase) should still match
    result = audit_env({"dbpassword": "s3cr3t"})
    assert len(result.errors) == 1


def test_access_key_pattern():
    result = audit_env({"AWS_ACCESS_KEY": "AKIAIOSFODNN7EXAMPLE"})
    assert len(result.errors) == 1
    assert result.errors[0].key == "AWS_ACCESS_KEY"
