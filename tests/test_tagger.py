"""Tests for envguard.tagger."""
import pytest
from envguard.tagger import tag_env, TagResult


@pytest.fixture
def _env():
    return {
        "AWS_ACCESS_KEY": "abc",
        "AWS_SECRET": "xyz",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DEBUG": "true",
        "APP_NAME": "myapp",
    }


def test_prefix_match_groups_aws_keys(_env):
    result = tag_env(_env, {"aws": ["AWS_"], "db": ["DB_"]})
    assert sorted(result.tags["aws"]) == ["AWS_ACCESS_KEY", "AWS_SECRET"]
    assert sorted(result.tags["db"]) == ["DB_HOST", "DB_PORT"]


def test_untagged_keys_collected(_env):
    result = tag_env(_env, {"aws": ["AWS_"]})
    assert "DEBUG" in result.untagged
    assert "APP_NAME" in result.untagged
    assert "DB_HOST" in result.untagged


def test_tag_names_sorted(_env):
    result = tag_env(_env, {"db": ["DB_"], "aws": ["AWS_"]})
    assert result.tag_names == ["aws", "db"]


def test_total_keys_matches_env(_env):
    result = tag_env(_env, {"aws": ["AWS_"], "db": ["DB_"]})
    assert result.total_keys == len(_env)


def test_key_tags_reverse_map(_env):
    result = tag_env(_env, {"aws": ["AWS_"], "db": ["DB_"]})
    assert "aws" in result.key_tags["AWS_ACCESS_KEY"]
    assert result.key_tags["DEBUG"] == []


def test_contains_mode_matches_substring():
    env = {"MY_TOKEN_VAL": "t", "API_KEY_MAIN": "k", "HOST": "h"}
    result = tag_env(env, {"secret": ["TOKEN", "KEY"]}, match_mode="contains")
    assert "MY_TOKEN_VAL" in result.tags["secret"]
    assert "API_KEY_MAIN" in result.tags["secret"]
    assert "HOST" in result.untagged


def test_empty_env_returns_empty_tags():
    result = tag_env({}, {"aws": ["AWS_"]})
    assert result.tags == {"aws": []}
    assert result.untagged == []
    assert result.total_keys == 0


def test_empty_rules_all_untagged(_env):
    result = tag_env(_env, {})
    assert len(result.untagged) == len(_env)


def test_summary_format(_env):
    result = tag_env(_env, {"aws": ["AWS_"], "db": ["DB_"]})
    s = result.summary()
    assert "aws(2)" in s
    assert "db(2)" in s
    assert "untagged=2" in s


def test_multiple_rules_same_tag():
    env = {"AWS_KEY": "a", "AZURE_KEY": "b", "GCP_KEY": "c"}
    result = tag_env(env, {"cloud": ["AWS_", "AZURE_", "GCP_"]})
    assert sorted(result.tags["cloud"]) == ["AWS_KEY", "AZURE_KEY", "GCP_KEY"]
    assert result.untagged == []
