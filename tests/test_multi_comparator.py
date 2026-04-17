"""Tests for multi_comparator."""
from pathlib import Path
import pytest

from envguard.multi_comparator import compare_many


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_no_differences(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\nB=2\n")
    t1 = _write(env_dir / "t1.env", "A=1\nB=2\n")
    results = compare_many(base, [t1])
    assert len(results) == 1
    assert not results[0].has_differences()


def test_missing_in_target(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\nB=2\n")
    t1 = _write(env_dir / "t1.env", "A=1\n")
    results = compare_many(base, [t1])
    assert "B" in results[0].missing_in_target


def test_multiple_targets(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\nB=2\n")
    t1 = _write(env_dir / "t1.env", "A=1\nB=2\n")
    t2 = _write(env_dir / "t2.env", "A=1\n")
    results = compare_many(base, [t1, t2])
    assert len(results) == 2
    assert not results[0].has_differences()
    assert results[1].has_differences()


def test_ignore_values(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=hello\n")
    t1 = _write(env_dir / "t1.env", "A=world\n")
    results = compare_many(base, [t1], ignore_values=True)
    assert not results[0].has_differences()


def test_ignore_extra(env_dir: Path) -> None:
    base = _write(env_dir / "base.env", "A=1\n")
    t1 = _write(env_dir / "t1.env", "A=1\nEXTRA=yes\n")
    results = compare_many(base, [t1], ignore_extra=True)
    assert not results[0].has_differences()
