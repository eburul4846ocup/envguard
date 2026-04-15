"""End-to-end integration: parse → capture → save → load → diff."""
from pathlib import Path

import pytest

from envguard.parser import parse_env_file
from envguard.snapshot import capture, load_snapshot, save_snapshot


@pytest.fixture()
def env_v1(tmp_path: Path) -> Path:
    p = tmp_path / ".env.v1"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "SECRET_KEY=abc123\n"
        "FEATURE_FLAG=false\n"
    )
    return p


@pytest.fixture()
def env_v2(tmp_path: Path) -> Path:
    p = tmp_path / ".env.v2"
    p.write_text(
        "DB_HOST=prod.db.example.com\n"
        "DB_PORT=5432\n"
        "SECRET_KEY=abc123\n"
        "NEW_RELIC_KEY=xyz\n"
    )
    return p


def test_full_pipeline(tmp_path, env_v1, env_v2):
    env1 = parse_env_file(env_v1)
    env2 = parse_env_file(env_v2)

    snap1 = capture(env1, source=str(env_v1), label="v1")
    snap2 = capture(env2, source=str(env_v2), label="v2")

    p1 = tmp_path / "snap1.json"
    p2 = tmp_path / "snap2.json"
    save_snapshot(snap1, p1)
    save_snapshot(snap2, p2)

    loaded1 = load_snapshot(p1)
    loaded2 = load_snapshot(p2)

    assert loaded2.keys_added_since(loaded1) == ["NEW_RELIC_KEY"]
    assert loaded2.keys_removed_since(loaded1) == ["FEATURE_FLAG"]
    assert loaded2.keys_changed_since(loaded1) == ["DB_HOST"]
    assert loaded2.has_changes_since(loaded1)


def test_identical_snapshots_report_no_changes(tmp_path, env_v1):
    env = parse_env_file(env_v1)
    s1 = capture(env, source=str(env_v1))
    s2 = capture(env, source=str(env_v1))

    p1 = tmp_path / "s1.json"
    p2 = tmp_path / "s2.json"
    save_snapshot(s1, p1)
    save_snapshot(s2, p2)

    l1 = load_snapshot(p1)
    l2 = load_snapshot(p2)

    assert not l2.has_changes_since(l1)
    assert l2.keys_added_since(l1) == []
    assert l2.keys_removed_since(l1) == []
    assert l2.keys_changed_since(l1) == []
