"""Tests for envguard.scanner."""
import pytest
from envguard.scanner import scan_env, ScanResult, ScanHit


def _env(**kwargs):
    return dict(kwargs)


def test_clean_env_returns_no_hits():
    result = scan_env(_env(APP_NAME="myapp", DEBUG="true", PORT="8080"))
    assert result.is_clean
    assert result.hit_count == 0


def test_empty_env_is_clean():
    result = scan_env({})
    assert result.is_clean


def test_aws_access_key_detected():
    result = scan_env(_env(AWS_KEY="AKIAIOSFODNN7EXAMPLE"))
    assert not result.is_clean
    assert result.hits[0].pattern_name == "aws_access_key"
    assert result.hits[0].key == "AWS_KEY"


def test_github_token_detected():
    result = scan_env(_env(GH_TOKEN="ghp_" + "A" * 36))
    assert not result.is_clean
    assert result.hits[0].pattern_name == "github_token"


def test_jwt_detected():
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    result = scan_env(_env(AUTH_TOKEN=token))
    assert not result.is_clean
    assert result.hits[0].pattern_name == "jwt"


def test_hex_secret_detected():
    result = scan_env(_env(SECRET_KEY="a3f1b2c4d5e6f7a8b9c0d1e2f3a4b5c6"))
    assert not result.is_clean


def test_empty_value_skipped():
    result = scan_env(_env(SECRET=""))
    assert result.is_clean


def test_hit_count_correct():
    result = scan_env(_env(
        AWS_KEY="AKIAIOSFODNN7EXAMPLE",
        PLAIN="hello",
        TOKEN="ghp_" + "B" * 36,
    ))
    assert result.hit_count == 2


def test_summary_clean():
    result = scan_env({})
    assert "No hardcoded" in result.summary()


def test_summary_with_hits():
    result = scan_env(_env(AWS_KEY="AKIAIOSFODNN7EXAMPLE"))
    summary = result.summary()
    assert "1 potential" in summary
    assert "aws_access_key" in summary


def test_str_hit_masks_value():
    hit = ScanHit(key="MY_KEY", value="supersecret", pattern_name="hex_secret")
    s = str(hit)
    assert "supe****" in s
    assert "supersecret" not in s
