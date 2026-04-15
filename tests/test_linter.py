"""Tests for envguard.linter."""
from pathlib import Path

import pytest

from envguard.linter import lint_env_file, LintIssue


@pytest.fixture
def env_file(tmp_path: Path):
    p = tmp_path / ".env"

    def _write(content: str) -> Path:
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_clean_file_has_no_issues(env_file):
    p = env_file("DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc123\n")
    result = lint_env_file(p)
    assert result.is_clean
    assert result.issues == []


def test_lowercase_key_produces_warning(env_file):
    p = env_file("database_url=postgres://localhost/db\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert 'W001' in codes


def test_require_uppercase_false_suppresses_w001(env_file):
    p = env_file("database_url=value\n")
    result = lint_env_file(p, require_uppercase=False)
    codes = [i.code for i in result.issues]
    assert 'W001' not in codes


def test_key_with_no_value_produces_warning(env_file):
    p = env_file("EMPTY_KEY=\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert 'W002' in codes


def test_warn_no_value_false_suppresses_w002(env_file):
    p = env_file("EMPTY_KEY=\n")
    result = lint_env_file(p, warn_no_value=False)
    codes = [i.code for i in result.issues]
    assert 'W002' not in codes


def test_duplicate_key_produces_warning(env_file):
    p = env_file("FOO=bar\nFOO=baz\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert 'W003' in codes


def test_invalid_line_produces_error(env_file):
    p = env_file("NOTAVALIDLINE\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert 'E001' in codes


def test_key_with_space_produces_error(env_file):
    p = env_file("BAD KEY=value\n")
    result = lint_env_file(p)
    codes = [i.code for i in result.issues]
    assert 'E002' in codes


def test_comments_and_blank_lines_ignored(env_file):
    p = env_file("# this is a comment\n\nVALID_KEY=value\n")
    result = lint_env_file(p)
    assert result.is_clean


def test_errors_and_warnings_split_correctly(env_file):
    p = env_file("NOTAVALIDLINE\nlowercase=val\n")
    result = lint_env_file(p)
    assert len(result.errors()) >= 1
    assert len(result.warnings()) >= 1


def test_lint_issue_str_format(env_file):
    p = env_file("bad line\n")
    result = lint_env_file(p)
    issue = result.issues[0]
    s = str(issue)
    assert 'E001' in s
    assert 'line 1' in s
