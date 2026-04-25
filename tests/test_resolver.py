"""Tests for envguard.resolver."""
from __future__ import annotations

import pytest
from envguard.resolver import resolve_envs, ResolveResult


def _r(*layers):
    return resolve_envs(list(layers))


class TestResolveClean:
    def test_no_references_returns_values_unchanged(self):
        result = _r({"HOST": "localhost", "PORT": "5432"})
        assert result.resolved == {"HOST": "localhost", "PORT": "5432"}

    def test_is_clean_when_no_missing_refs(self):
        result = _r({"A": "hello"})
        assert result.is_clean is True

    def test_total_keys_counts_all_resolved_keys(self):
        result = _r({"A": "1", "B": "2", "C": "3"})
        assert result.total_keys == 3

    def test_summary_clean(self):
        result = _r({"X": "val"})
        assert "no unresolved" in result.summary()


class TestResolveExpansion:
    def test_curly_brace_reference_expanded(self):
        result = _r({"BASE": "http://localhost", "URL": "${BASE}/api"})
        assert result.resolved["URL"] == "http://localhost/api"

    def test_bare_dollar_reference_expanded(self):
        result = _r({"HOST": "db", "DSN": "postgres://$HOST/mydb"})
        assert result.resolved["DSN"] == "postgres://db/mydb"

    def test_multiple_references_in_one_value(self):
        result = _r({"H": "host", "P": "5432", "DSN": "${H}:${P}"})
        assert result.resolved["DSN"] == "host:5432"

    def test_cross_layer_reference_resolved(self):
        base = {"HOST": "localhost"}
        override = {"URL": "${HOST}/path"}
        result = _r(base, override)
        assert result.resolved["URL"] == "localhost/path"

    def test_later_layer_overrides_earlier(self):
        base = {"KEY": "base_val"}
        override = {"KEY": "override_val"}
        result = _r(base, override)
        assert result.resolved["KEY"] == "override_val"

    def test_override_layer_value_used_in_reference(self):
        base = {"HOST": "old", "URL": "${HOST}/api"}
        override = {"HOST": "new"}
        result = _r(base, override)
        assert result.resolved["URL"] == "new/api"


class TestResolveUnresolved:
    def test_missing_reference_kept_in_value(self):
        result = _r({"URL": "${MISSING}/path"})
        assert "${MISSING}" in result.resolved["URL"]

    def test_missing_reference_recorded(self):
        result = _r({"URL": "${MISSING}/path"})
        assert "URL" in result.unresolved_refs
        assert "MISSING" in result.unresolved_refs["URL"]

    def test_is_clean_false_when_missing_refs(self):
        result = _r({"A": "${GHOST}"})
        assert result.is_clean is False

    def test_summary_reports_unresolved_count(self):
        result = _r({"A": "${X}", "B": "${Y}"})
        assert "unresolved" in result.summary()

    def test_clean_keys_unaffected_by_sibling_missing_ref(self):
        result = _r({"GOOD": "plain", "BAD": "${NOPE}"})
        assert result.resolved["GOOD"] == "plain"


class TestEdgeCases:
    def test_empty_layers_returns_empty_result(self):
        result = resolve_envs([])
        assert result.resolved == {}
        assert result.is_clean is True

    def test_single_empty_layer(self):
        result = _r({})
        assert result.resolved == {}

    def test_value_with_no_dollar_sign_untouched(self):
        result = _r({"PATH": "/usr/local/bin"})
        assert result.resolved["PATH"] == "/usr/local/bin"
