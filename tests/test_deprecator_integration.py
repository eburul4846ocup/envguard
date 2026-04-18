"""Integration tests: parse a real file then run deprecation check."""
import pytest
from pathlib import Path
from envguard.parser import parse_env_file
from envguard.deprecator import check_deprecations


@pytest.fixture()
def tmp_env(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, content: str):
    path.write_text(content)


def test_full_pipeline_no_issues(tmp_env):
    _write(tmp_env, "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=abc\n")
    env = parse_env_file(tmp_env)
    result = check_deprecations(env, {"OLD_DB": "DATABASE_URL"})
    assert result.is_clean
    assert result.checked == 2


def test_full_pipeline_detects_deprecated(tmp_env):
    _write(tmp_env, "OLD_DB=postgres://localhost/db\nSECRET_KEY=abc\n")
    env = parse_env_file(tmp_env)
    result = check_deprecations(env, {"OLD_DB": "DATABASE_URL"})
    assert not result.is_clean
    assert result.issues[0].key == "OLD_DB"
    assert result.issues[0].replacement == "DATABASE_URL"


def test_quoted_values_still_detected(tmp_env):
    _write(tmp_env, 'LEGACY_HOST="old.host.com"\n')
    env = parse_env_file(tmp_env)
    result = check_deprecations(env, {"LEGACY_HOST": "HOST"})
    assert result.issue_count == 1


def test_empty_map_always_clean(tmp_env):
    _write(tmp_env, "A=1\nB=2\nC=3\n")
    env = parse_env_file(tmp_env)
    result = check_deprecations(env, {})
    assert result.is_clean
    assert result.checked == 3
