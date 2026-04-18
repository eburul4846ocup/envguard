"""Tests for envguard.deprecator."""
import pytest
from envguard.deprecator import check_deprecations, DeprecationIssue, DeprecationResult


def _env(**kwargs):
    return {k: v for k, v in kwargs.items()}


def test_clean_env_no_issues():
    result = check_deprecations(_env(HOST="localhost", PORT="5432"), {})
    assert result.is_clean
    assert result.issue_count == 0


def test_deprecated_key_detected():
    result = check_deprecations(
        _env(OLD_DB_URL="postgres://"),
        {"OLD_DB_URL": "DATABASE_URL"},
    )
    assert not result.is_clean
    assert result.issue_count == 1
    assert result.issues[0].key == "OLD_DB_URL"
    assert result.issues[0].replacement == "DATABASE_URL"


def test_deprecated_key_without_replacement():
    result = check_deprecations(
        _env(LEGACY_FLAG="1"),
        {"LEGACY_FLAG": None},
    )
    assert result.issue_count == 1
    assert result.issues[0].replacement is None


def test_multiple_deprecated_keys():
    result = check_deprecations(
        _env(OLD_HOST="h", OLD_PORT="p", NEW_KEY="v"),
        {"OLD_HOST": "HOST", "OLD_PORT": "PORT"},
    )
    assert result.issue_count == 2
    assert result.checked == 3


def test_checked_count_matches_env_size():
    result = check_deprecations(_env(A="1", B="2", C="3"), {})
    assert result.checked == 3


def test_summary_clean():
    result = check_deprecations(_env(X="1"), {})
    assert "No deprecated" in result.summary()
    assert "1 keys checked" in result.summary()


def test_summary_with_issues():
    result = check_deprecations(_env(OLD="v"), {"OLD": "NEW"})
    assert "1 deprecated" in result.summary()


def test_issue_str_with_replacement():
    issue = DeprecationIssue(key="OLD", replacement="NEW")
    assert "OLD" in str(issue)
    assert "NEW" in str(issue)


def test_issue_str_without_replacement():
    issue = DeprecationIssue(key="OLD", replacement=None)
    assert "OLD" in str(issue)
    assert "use" not in str(issue)
