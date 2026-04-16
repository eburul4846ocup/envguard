"""Tests for envguard.encryptor."""
import pytest
from envguard.encryptor import encrypt_env, decrypt_env, EncryptResult, _is_sensitive


def _env():
    return {
        "API_KEY": "abc123",
        "DB_PASSWORD": "s3cr3t",
        "APP_NAME": "myapp",
        "DEBUG": "true",
    }


def test_is_sensitive_detects_key():
    assert _is_sensitive("API_KEY") is True


def test_is_sensitive_detects_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_ignores_plain():
    assert _is_sensitive("APP_NAME") is False


def test_encrypt_returns_encrypt_result():
    result = encrypt_env(_env(), "passphrase")
    assert isinstance(result, EncryptResult)


def test_sensitive_values_are_encrypted():
    env = _env()
    result = encrypt_env(env, "passphrase")
    assert result.encrypted["API_KEY"] != env["API_KEY"]
    assert result.encrypted["DB_PASSWORD"] != env["DB_PASSWORD"]


def test_non_sensitive_values_unchanged():
    result = encrypt_env(_env(), "passphrase")
    assert result.encrypted["APP_NAME"] == "myapp"
    assert result.encrypted["DEBUG"] == "true"


def test_processed_and_skipped_lists():
    result = encrypt_env(_env(), "passphrase")
    assert "API_KEY" in result.processed
    assert "DB_PASSWORD" in result.processed
    assert "APP_NAME" in result.skipped


def test_encrypt_count():
    result = encrypt_env(_env(), "passphrase")
    assert result.encrypt_count == 2


def test_summary_string():
    result = encrypt_env(_env(), "passphrase")
    assert "Encrypted 2" in result.summary()


def test_decrypt_recovers_original():
    env = _env()
    encrypted = encrypt_env(env, "mypassword")
    decrypted = decrypt_env(encrypted.encrypted, "mypassword")
    assert decrypted["API_KEY"] == "abc123"
    assert decrypted["DB_PASSWORD"] == "s3cr3t"


def test_decrypt_leaves_plain_unchanged():
    env = _env()
    encrypted = encrypt_env(env, "mypassword")
    decrypted = decrypt_env(encrypted.encrypted, "mypassword")
    assert decrypted["APP_NAME"] == "myapp"


def test_all_keys_flag_encrypts_everything():
    env = _env()
    result = encrypt_env(env, "pass", all_keys=True)
    assert result.encrypt_count == len(env)
    assert len(result.skipped) == 0


def test_wrong_passphrase_does_not_recover():
    env = {"API_KEY": "secret"}
    encrypted = encrypt_env(env, "correct")
    decrypted = decrypt_env(encrypted.encrypted, "wrong")
    assert decrypted["API_KEY"] != "secret"
