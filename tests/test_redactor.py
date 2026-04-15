"""Tests for envguard.redactor."""
import pytest
from envguard.redactor import redact_env, RedactionResult, DEFAULT_MASK, _is_sensitive


# ---------------------------------------------------------------------------
# _is_sensitive helper
# ---------------------------------------------------------------------------

def test_secret_key_is_sensitive():
    assert _is_sensitive("APP_SECRET") is True


def test_password_key_is_sensitive():
    assert _is_sensitive("DB_PASSWORD") is True


def test_token_key_is_sensitive():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_plain_key_is_not_sensitive():
    assert _is_sensitive("APP_NAME") is False


def test_debug_key_is_not_sensitive():
    assert _is_sensitive("DEBUG") is False


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_non_sensitive_values_unchanged():
    env = {"APP_NAME": "myapp", "PORT": "8080"}
    result = redact_env(env)
    assert result.redacted == env
    assert result.redacted_keys == []


def test_sensitive_value_replaced_with_default_mask():
    env = {"DB_PASSWORD": "s3cr3t", "HOST": "localhost"}
    result = redact_env(env)
    assert result.redacted["DB_PASSWORD"] == DEFAULT_MASK
    assert result.redacted["HOST"] == "localhost"


def test_redacted_keys_list_populated():
    env = {"API_KEY": "abc", "SECRET_TOKEN": "xyz", "NAME": "bob"}
    result = redact_env(env)
    assert "API_KEY" in result.redacted_keys
    assert "SECRET_TOKEN" in result.redacted_keys
    assert "NAME" not in result.redacted_keys


def test_custom_mask_used():
    env = {"APP_SECRET": "hunter2"}
    result = redact_env(env, mask="<hidden>")
    assert result.redacted["APP_SECRET"] == "<hidden>"


def test_extra_keys_always_redacted():
    env = {"PLAIN_KEY": "value", "ANOTHER": "data"}
    result = redact_env(env, extra_keys={"PLAIN_KEY"})
    assert result.redacted["PLAIN_KEY"] == DEFAULT_MASK
    assert result.redacted["ANOTHER"] == "data"


def test_extra_keys_case_insensitive():
    env = {"plain_key": "value"}
    result = redact_env(env, extra_keys={"PLAIN_KEY"})
    assert result.redacted["plain_key"] == DEFAULT_MASK


def test_original_not_mutated():
    env = {"DB_PASSWORD": "secret"}
    result = redact_env(env)
    assert result.original["DB_PASSWORD"] == "secret"


def test_redaction_count():
    env = {"A_SECRET": "x", "B_TOKEN": "y", "SAFE": "z"}
    result = redact_env(env)
    assert result.redaction_count == 2


def test_summary_no_redactions():
    result = redact_env({"APP": "val"})
    assert result.summary() == "No sensitive keys redacted."


def test_summary_with_redactions():
    env = {"DB_PASSWORD": "pw", "API_KEY": "k"}
    result = redact_env(env)
    assert "2 sensitive key(s)" in result.summary()
    assert "API_KEY" in result.summary()
    assert "DB_PASSWORD" in result.summary()
