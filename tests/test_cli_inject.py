"""CLI tests for `envguard inject`."""
import argparse
import os
from pathlib import Path

import pytest

from envguard.cli_inject import _run_inject


@pytest.fixture()
def env_file(tmp_path: Path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _args(**kw) -> argparse.Namespace:
    defaults = dict(source=None, target=None, override=False, keys=None, fmt="text")
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_inject_exits_zero_for_valid_file(env_file: Path):
    _write(env_file, "FOO=bar\nBAZ=qux\n")
    rc = _run_inject(_args(source=str(env_file), target=str(env_file)))
    assert rc == 0


def test_inject_missing_source_exits_two(tmp_path: Path):
    rc = _run_inject(_args(source=str(tmp_path / "ghost.env")))
    assert rc == 2


def test_inject_missing_target_exits_two(env_file: Path, tmp_path: Path):
    _write(env_file, "A=1\n")
    rc = _run_inject(_args(source=str(env_file), target=str(tmp_path / "ghost.env")))
    assert rc == 2


def test_inject_json_output_contains_summary(env_file: Path, capsys):
    _write(env_file, "HELLO=world\n")
    target_file = env_file.parent / ".env.target"
    _write(target_file, "OTHER=val\n")
    rc = _run_inject(_args(source=str(env_file), target=str(target_file), fmt="json"))
    assert rc == 0
    out = capsys.readouterr().out
    import json
    data = json.loads(out)
    assert "summary" in data
    assert "injected" in data


def test_inject_skips_existing_without_override(env_file: Path, capsys):
    _write(env_file, "KEY=new\n")
    target_file = env_file.parent / ".env.t"
    _write(target_file, "KEY=old\n")
    rc = _run_inject(_args(source=str(env_file), target=str(target_file), fmt="json"))
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert "KEY" in data["skipped"]
    assert "KEY" not in data["injected"]


def test_inject_override_flag_overrides_existing(env_file: Path, capsys):
    _write(env_file, "KEY=new\n")
    target_file = env_file.parent / ".env.t"
    _write(target_file, "KEY=old\n")
    rc = _run_inject(
        _args(source=str(env_file), target=str(target_file), override=True, fmt="json")
    )
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert data["overridden"].get("KEY") == "new"


def test_inject_keys_filter_limits_output(env_file: Path, capsys):
    _write(env_file, "A=1\nB=2\nC=3\n")
    target_file = env_file.parent / ".env.t"
    _write(target_file, "")
    rc = _run_inject(
        _args(source=str(env_file), target=str(target_file), keys=["A"], fmt="json")
    )
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert "A" in data["injected"]
    assert "B" not in data["injected"]
    assert "C" not in data["injected"]
