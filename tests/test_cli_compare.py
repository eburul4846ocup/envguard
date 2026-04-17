"""Tests for cli_compare._run_compare."""
from pathlib import Path
import argparse
import pytest

from envguard.cli_compare import _run_compare


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _args(baseline: Path, targets, fmt: str = "text", ignore_values: bool = False,
          ignore_extra: bool = False, no_color: bool = True) -> argparse.Namespace:
    return argparse.Namespace(
        baseline=baseline, targets=list(targets), fmt=fmt,
        ignore_values=ignore_values, ignore_extra=ignore_extra, no_color=no_color,
    )


def test_no_differences_exits_zero(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\n")
    t1 = _write(env_dir / "t1.env", "A=1\n")
    assert _run_compare(_args(base, [t1])) == 0


def test_differences_exits_one(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\nB=2\n")
    t1 = _write(env_dir / "t1.env", "A=1\n")
    assert _run_compare(_args(base, [t1])) == 1


def test_missing_baseline_exits_two(env_dir: Path) -> None:
    base = env_dir / "ghost.env"
    t1 = _write(env_dir / "t1.env", "A=1\n")
    assert _run_compare(_args(base, [t1])) == 2


def test_missing_target_exits_two(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\n")
    t1 = env_dir / "ghost.env"
    assert _run_compare(_args(base, [t1])) == 2


def test_json_output(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    base = _write(env_dir / "base.env", "A=1\n")
    t1 = _write(env_dir / "t1.env", "A=1\n")
    _run_compare(_args(base, [t1], fmt="json"))
    out = capsys.readouterr().out
    assert "source" in out
    assert "missing_in_target" in out
