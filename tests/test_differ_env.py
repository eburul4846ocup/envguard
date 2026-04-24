"""Tests for envguard.differ_env module."""
from __future__ import annotations

import pytest
from pathlib import Path

from envguard.differ_env import diff_many, EnvKeyReport, MultiEnvDiff


@pytest.fixture()
def tmp_envs(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def test_no_issues_when_identical(tmp_envs):
    p1 = tmp_envs(".env.dev", "KEY=value\nDB=postgres\n")
    p2 = tmp_envs(".env.prod", "KEY=value\nDB=postgres\n")
    diff = diff_many({"dev": p1, "prod": p2})
    assert not diff.has_issues


def test_missing_key_detected(tmp_envs):
    p1 = tmp_envs(".env.dev", "KEY=value\nEXTRA=only_dev\n")
    p2 = tmp_envs(".env.prod", "KEY=value\n")
    diff = diff_many({"dev": p1, "prod": p2})
    assert diff.has_issues
    gap_keys = [r.key for r in diff.keys_with_gaps]
    assert "EXTRA" in gap_keys


def test_value_mismatch_detected(tmp_envs):
    p1 = tmp_envs(".env.dev", "KEY=dev_value\n")
    p2 = tmp_envs(".env.prod", "KEY=prod_value\n")
    diff = diff_many({"dev": p1, "prod": p2})
    assert diff.has_issues
    inconsistent = [r.key for r in diff.inconsistent_keys]
    assert "KEY" in inconsistent


def test_consistent_key_not_in_inconsistent(tmp_envs):
    p1 = tmp_envs(".env.dev", "KEY=same\n")
    p2 = tmp_envs(".env.prod", "KEY=same\n")
    diff = diff_many({"dev": p1, "prod": p2})
    assert diff.inconsistent_keys == []


def test_env_names_preserved(tmp_envs):
    p1 = tmp_envs(".env.a", "X=1\n")
    p2 = tmp_envs(".env.b", "X=1\n")
    diff = diff_many({"alpha": p1, "beta": p2})
    assert "alpha" in diff.env_names
    assert "beta" in diff.env_names


def test_missing_in_property(tmp_envs):
    p1 = tmp_envs(".env.dev", "ONLY_DEV=1\n")
    p2 = tmp_envs(".env.prod", "")
    diff = diff_many({"dev": p1, "prod": p2})
    report = next(r for r in diff.reports if r.key == "ONLY_DEV")
    assert "prod" in report.missing_in
    assert "dev" not in report.missing_in


def test_summary_contains_counts(tmp_envs):
    p1 = tmp_envs(".env.dev", "A=1\nB=x\n")
    p2 = tmp_envs(".env.prod", "A=1\nB=y\n")
    diff = diff_many({"dev": p1, "prod": p2})
    s = diff.summary()
    assert "2" in s
    assert "2" in s  # 2 environments


def test_three_environments(tmp_envs):
    p1 = tmp_envs(".env.dev", "A=1\nB=2\n")
    p2 = tmp_envs(".env.stg", "A=1\nB=2\n")
    p3 = tmp_envs(".env.prod", "A=1\n")
    diff = diff_many({"dev": p1, "stg": p2, "prod": p3})
    assert diff.has_issues
    gap = next(r for r in diff.keys_with_gaps if r.key == "B")
    assert "prod" in gap.missing_in
