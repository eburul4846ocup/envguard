"""Tests for envguard.masker."""
import pytest
from envguard.masker import mask_env, MaskResult, _is_sensitive


# --- _is_sensitive ---

def test_secret_key_is_sensitive():
    assert _is_sensitive("APP_SECRET") is True

def test_password_key_is_sensitive():
    assert _is_sensitive("DB_PASSWORD") is True

def test_token_key_is_sensitive():
    assert _is_sensitive("GITHUB_TOKEN") is True

def test_plain_key_not_sensitive():
    assert _is_sensitive("APP_NAME") is False

def test_debug_key_not_sensitive():
    assert _is_sensitive("DEBUG") is False


# --- mask_env ---

def _env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "true",
    }


def test_plain_keys_unchanged():
    result = mask_env(_env())
    assert result.masked["APP_NAME"] == "myapp"
    assert result.masked["DEBUG"] == "true"


def test_sensitive_keys_masked():
    result = mask_env(_env())
    assert result.masked["DB_PASSWORD"] == "******"
    assert result.masked["API_KEY"] == "******"


def test_mask_count():
    result = mask_env(_env())
    assert result.mask_count == 2


def test_masked_keys_set():
    result = mask_env(_env())
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys


def test_is_changed_true_when_sensitive_present():
    assert mask_env(_env()).is_changed is True


def test_is_changed_false_when_no_sensitive():
    result = mask_env({"APP_NAME": "x", "DEBUG": "1"})
    assert result.is_changed is False


def test_visible_chars_shows_suffix():
    result = mask_env({"API_KEY": "abcdef"}, visible_chars=2)
    assert result.masked["API_KEY"] == "****ef"


def test_custom_keys_treated_as_sensitive():
    result = mask_env({"MY_VAR": "hello"}, custom_keys={"MY_VAR"})
    assert result.masked["MY_VAR"] == "******"
    assert "MY_VAR" in result.masked_keys


def test_summary_no_masked():
    result = mask_env({"APP": "x"})
    assert "nothing masked" in result.summary()


def test_summary_with_masked():
    result = mask_env(_env())
    assert "2 key(s) masked" in result.summary()


def test_short_value_gets_minimum_mask_length():
    result = mask_env({"DB_PASSWORD": "hi"})
    assert result.masked["DB_PASSWORD"] == "******"
