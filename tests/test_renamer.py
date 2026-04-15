"""Tests for envguard.renamer."""
import pytest
from envguard.renamer import rename_env, RenameResult


def _env(**kwargs: str):
    return dict(kwargs)


class TestRenameEnv:
    def test_single_rename_applied(self):
        result = rename_env(_env(OLD_KEY="value"), {"OLD_KEY": "NEW_KEY"})
        assert "NEW_KEY" in result.renamed
        assert "OLD_KEY" not in result.renamed
        assert result.renamed["NEW_KEY"] == "value"

    def test_rename_count_correct(self):
        result = rename_env(
            _env(A="1", B="2"),
            {"A": "ALPHA", "B": "BETA"},
        )
        assert result.rename_count == 2

    def test_missing_key_goes_to_skipped(self):
        result = rename_env(_env(EXISTING="yes"), {"MISSING": "NEW"})
        assert "MISSING" in result.skipped
        assert result.rename_count == 0

    def test_unaffected_keys_preserved(self):
        result = rename_env(
            _env(KEEP="kept", CHANGE="val"),
            {"CHANGE": "CHANGED"},
        )
        assert result.renamed["KEEP"] == "kept"
        assert "CHANGED" in result.renamed

    def test_empty_env_returns_empty_renamed(self):
        result = rename_env({}, {"A": "B"})
        assert result.renamed == {}
        assert result.skipped == ["A"]

    def test_empty_mapping_returns_original_env(self):
        env = _env(X="1", Y="2")
        result = rename_env(env, {})
        assert result.renamed == env
        assert result.rename_count == 0

    def test_applied_contains_old_new_pairs(self):
        result = rename_env(_env(FOO="bar"), {"FOO": "BAR"})
        assert ("FOO", "BAR") in result.applied

    def test_original_env_not_mutated(self):
        env = _env(OLD="v")
        rename_env(env, {"OLD": "NEW"})
        assert "OLD" in env  # original unchanged


class TestRenameResultSummary:
    def test_summary_shows_rename_count(self):
        result = rename_env(_env(A="1"), {"A": "B"})
        assert "1" in result.summary()

    def test_summary_shows_skipped_keys(self):
        result = rename_env({}, {"GHOST": "SPIRIT"})
        assert "GHOST" in result.summary()

    def test_summary_no_skipped_omits_skipped_line(self):
        result = rename_env(_env(K="v"), {"K": "KEY"})
        assert "Skipped" not in result.summary()
