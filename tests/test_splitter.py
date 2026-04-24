"""Tests for envguard.splitter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envguard.splitter import SplitResult, split_env, write_split


def _env(**kwargs: str) -> dict:
    return dict(kwargs)


# ---------------------------------------------------------------------------
# split_env – auto-detect mode
# ---------------------------------------------------------------------------

class TestAutoDetect:
    def test_empty_env_returns_empty_result(self):
        result = split_env({})
        assert result.total_keys == 0
        assert result.group_names == []
        assert result.ungrouped == {}

    def test_keys_without_separator_go_to_ungrouped(self):
        result = split_env({"DEBUG": "true", "PORT": "8080"})
        assert result.ungrouped == {"DEBUG": "true", "PORT": "8080"}
        assert result.groups == {}

    def test_shared_prefix_forms_group(self):
        env = {"AWS_KEY": "k", "AWS_SECRET": "s", "PORT": "80"}
        result = split_env(env)
        assert "AWS" in result.group_names
        assert result.groups["AWS"] == {"AWS_KEY": "k", "AWS_SECRET": "s"}
        assert result.ungrouped == {"PORT": "80"}

    def test_lone_prefixed_key_goes_to_ungrouped(self):
        env = {"DB_HOST": "localhost", "PORT": "5432"}
        result = split_env(env)
        # DB_HOST is the only DB_ key → ungrouped
        assert "DB_HOST" in result.ungrouped
        assert "PORT" in result.ungrouped
        assert result.groups == {}

    def test_multiple_groups_detected(self):
        env = {
            "AWS_KEY": "k",
            "AWS_SECRET": "s",
            "DB_HOST": "h",
            "DB_PORT": "5432",
        }
        result = split_env(env)
        assert set(result.group_names) == {"AWS", "DB"}
        assert result.ungrouped == {}

    def test_total_keys_accounts_for_all(self):
        env = {"AWS_KEY": "k", "AWS_SECRET": "s", "PORT": "80"}
        result = split_env(env)
        assert result.total_keys == 3


# ---------------------------------------------------------------------------
# split_env – explicit prefixes mode
# ---------------------------------------------------------------------------

class TestExplicitPrefixes:
    def test_explicit_prefix_groups_matching_keys(self):
        env = {"AWS_KEY": "k", "AWS_SECRET": "s", "PORT": "80"}
        result = split_env(env, prefixes=["AWS"])
        assert result.groups["AWS"] == {"AWS_KEY": "k", "AWS_SECRET": "s"}
        assert result.ungrouped == {"PORT": "80"}

    def test_unmatched_keys_go_to_ungrouped(self):
        env = {"REDIS_HOST": "localhost", "PORT": "6379"}
        result = split_env(env, prefixes=["AWS"])
        assert result.ungrouped == {"REDIS_HOST": "localhost", "PORT": "6379"}
        assert result.groups == {}

    def test_prefix_matching_is_case_insensitive(self):
        env = {"aws_key": "k", "aws_secret": "s"}
        result = split_env(env, prefixes=["aws"])
        assert "AWS" in result.groups


# ---------------------------------------------------------------------------
# SplitResult helpers
# ---------------------------------------------------------------------------

def test_file_count_no_ungrouped():
    result = SplitResult(groups={"AWS": {"AWS_KEY": "k"}})
    assert result.file_count == 1


def test_file_count_with_ungrouped():
    result = SplitResult(
        groups={"AWS": {"AWS_KEY": "k"}},
        ungrouped={"PORT": "80"},
    )
    assert result.file_count == 2


def test_summary_string():
    result = SplitResult(
        groups={"AWS": {"AWS_KEY": "k", "AWS_SECRET": "s"}},
        ungrouped={"PORT": "80"},
    )
    summary = result.summary()
    assert "AWS: 2 key(s)" in summary
    assert "ungrouped: 1 key(s)" in summary


def test_summary_empty():
    assert SplitResult().summary() == "no keys"


# ---------------------------------------------------------------------------
# write_split
# ---------------------------------------------------------------------------

def test_write_split_creates_files(tmp_path: Path):
    env = {"AWS_KEY": "k", "AWS_SECRET": "s", "PORT": "80"}
    result = split_env(env)
    written = write_split(result, tmp_path)
    filenames = {p.name for p in written}
    assert ".env.aws" in filenames
    assert ".env.misc" in filenames


def test_write_split_file_content(tmp_path: Path):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = split_env(env)
    write_split(result, tmp_path)
    content = (tmp_path / ".env.db").read_text()
    assert "DB_HOST=localhost" in content
    assert "DB_PORT=5432" in content


def test_write_split_custom_ungrouped_name(tmp_path: Path):
    env = {"PORT": "80"}
    result = split_env(env)
    write_split(result, tmp_path, ungrouped_name=".env.other")
    assert (tmp_path / ".env.other").exists()


def test_write_split_returns_written_paths(tmp_path: Path):
    env = {"AWS_KEY": "k", "AWS_SECRET": "s"}
    result = split_env(env)
    written = write_split(result, tmp_path)
    assert all(isinstance(p, Path) for p in written)
    assert all(p.exists() for p in written)
