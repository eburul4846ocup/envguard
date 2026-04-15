"""Integration tests for the snapshot CLI sub-commands."""
import json
from pathlib import Path

import pytest

from envguard.cli_snapshot import _run_snapshot


@pytest.fixture()
def env_dir(tmp_path: Path):
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def _make_args(**kwargs):
    """Minimal namespace factory."""
    import argparse
    defaults = {"snapshot_cmd": "capture", "label": None, "no_values": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCaptureCLI:
    def test_capture_creates_file(self, env_dir):
        env_file = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
        out = env_dir / "snap.json"
        args = _make_args(snapshot_cmd="capture", env_file=str(env_file), output=str(out))
        rc = _run_snapshot(args)
        assert rc == 0
        assert out.exists()

    def test_capture_json_contains_keys(self, env_dir):
        env_file = _write(env_dir / ".env", "A=1\nB=2\n")
        out = env_dir / "snap.json"
        args = _make_args(snapshot_cmd="capture", env_file=str(env_file), output=str(out))
        _run_snapshot(args)
        data = json.loads(out.read_text())
        assert data["env"] == {"A": "1", "B": "2"}

    def test_capture_label_stored(self, env_dir):
        env_file = _write(env_dir / ".env", "X=y\n")
        out = env_dir / "snap.json"
        args = _make_args(snapshot_cmd="capture", env_file=str(env_file),
                          output=str(out), label="release-1")
        _run_snapshot(args)
        data = json.loads(out.read_text())
        assert data["label"] == "release-1"


class TestDiffCLI:
    def _make_snaps(self, env_dir, prev_content, curr_content):
        from envguard.snapshot import capture, save_snapshot
        from envguard.parser import parse_env_file

        prev_f = _write(env_dir / "prev.env", prev_content)
        curr_f = _write(env_dir / "curr.env", curr_content)
        p_snap = env_dir / "prev.json"
        c_snap = env_dir / "curr.json"
        save_snapshot(capture(parse_env_file(prev_f), source=str(prev_f)), p_snap)
        save_snapshot(capture(parse_env_file(curr_f), source=str(curr_f)), c_snap)
        return str(p_snap), str(c_snap)

    def test_diff_no_changes_exits_zero(self, env_dir):
        p, c = self._make_snaps(env_dir, "K=v\n", "K=v\n")
        args = _make_args(snapshot_cmd="diff", previous=p, current=c)
        assert _run_snapshot(args) == 0

    def test_diff_with_changes_exits_one(self, env_dir):
        p, c = self._make_snaps(env_dir, "K=old\n", "K=new\n")
        args = _make_args(snapshot_cmd="diff", previous=p, current=c)
        assert _run_snapshot(args) == 1

    def test_diff_added_key(self, env_dir, capsys):
        p, c = self._make_snaps(env_dir, "A=1\n", "A=1\nB=2\n")
        args = _make_args(snapshot_cmd="diff", previous=p, current=c)
        _run_snapshot(args)
        out = capsys.readouterr().out
        assert "+ B" in out

    def test_diff_removed_key(self, env_dir, capsys):
        p, c = self._make_snaps(env_dir, "A=1\nB=2\n", "A=1\n")
        args = _make_args(snapshot_cmd="diff", previous=p, current=c)
        _run_snapshot(args)
        out = capsys.readouterr().out
        assert "- B" in out

    def test_diff_no_values_flag(self, env_dir, capsys):
        p, c = self._make_snaps(env_dir, "SECRET=hunter2\n", "SECRET=newpass\n")
        args = _make_args(snapshot_cmd="diff", previous=p, current=c, no_values=True)
        _run_snapshot(args)
        out = capsys.readouterr().out
        assert "hunter2" not in out
        assert "newpass" not in out
