"""Tests for envguard.flattener."""
import pytest
from envguard.flattener import flatten_env, FlattenResult


@pytest.fixture()
def _env():
    return {
        "db.host": "localhost",
        "db.port": "5432",
        "APP_NAME": "myapp",
        "cache.ttl": "300",
    }


class TestFlattenEnvDefaults:
    def test_dotted_keys_replaced_with_underscore(self, _env):
        result = flatten_env(_env)
        assert "DB_HOST" in result.flattened
        assert "DB_PORT" in result.flattened
        assert "CACHE_TTL" in result.flattened

    def test_plain_key_preserved(self, _env):
        result = flatten_env(_env)
        assert "APP_NAME" in result.flattened

    def test_original_dotted_keys_absent(self, _env):
        result = flatten_env(_env)
        for key in result.flattened:
            assert "." not in key

    def test_values_unchanged(self, _env):
        result = flatten_env(_env)
        assert result.flattened["DB_HOST"] == "localhost"
        assert result.flattened["APP_NAME"] == "myapp"

    def test_renamed_list_contains_dotted_keys(self, _env):
        result = flatten_env(_env)
        assert set(result.renamed) == {"db.host", "db.port", "cache.ttl"}

    def test_change_count_equals_renamed_length(self, _env):
        result = flatten_env(_env)
        assert result.change_count == len(result.renamed)

    def test_is_changed_true_when_dotted_keys_present(self, _env):
        result = flatten_env(_env)
        assert result.is_changed is True

    def test_is_changed_false_when_no_dotted_keys(self):
        result = flatten_env({"FOO": "bar", "BAZ": "qux"})
        assert result.is_changed is False


class TestFlattenEnvOptions:
    def test_custom_from_sep(self):
        env = {"db__host": "localhost", "db__port": "5432"}
        result = flatten_env(env, from_sep="__", to_sep="_")
        assert "DB_HOST" in result.flattened
        assert result.change_count == 2

    def test_custom_to_sep(self):
        env = {"db.host": "localhost"}
        result = flatten_env(env, from_sep=".", to_sep="-")
        assert "DB-HOST" in result.flattened

    def test_uppercase_false_preserves_case(self):
        env = {"db.host": "localhost"}
        result = flatten_env(env, uppercase=False)
        assert "db_host" in result.flattened

    def test_empty_env_returns_empty_result(self):
        result = flatten_env({})
        assert result.flattened == {}
        assert result.change_count == 0
        assert result.is_changed is False


class TestFlattenResultHelpers:
    def test_summary_no_changes(self):
        result = flatten_env({"FOO": "bar"})
        assert "No keys" in result.summary()

    def test_summary_with_changes(self):
        result = flatten_env({"a.b": "val"})
        assert "flattened" in result.summary()

    def test_to_string_produces_key_equals_value_lines(self):
        result = flatten_env({"a.b": "val", "FOO": "bar"})
        lines = result.to_string().splitlines()
        assert any("=val" in ln for ln in lines)
        assert any("FOO=bar" in ln for ln in lines)

    def test_original_is_unchanged_copy(self):
        env = {"a.b": "1"}
        result = flatten_env(env)
        assert result.original == {"a.b": "1"}
        assert "a.b" not in result.flattened
