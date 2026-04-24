"""CLI tests for the 'flatten' sub-command."""
import argparse
from pathlib import Path

import pytest

from envguard.cli_flatten import _run_flatten


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    return tmp_path / ".env"


def _write(p: Path, content: str) -> None:
    p.write_text(content, encoding="utf-8")


def _args(file: str, **kwargs) -> argparse.Namespace:
    defaults = {
        "from_sep": ".",
        "to_sep": "_",
        "no_uppercase": False,
        "in_place": False,
    }
    defaults.update(kwargs)
    defaults["file"] = file
    return argparse.Namespace(**defaults)


class TestFlattenCLI:
    def test_exits_zero_when_no_dotted_keys(self, env_file: Path):
        _write(env_file, "FOO=bar\nBAZ=qux\n")
        assert _run_flatten(_args(str(env_file))) == 0

    def test_exits_one_when_dotted_keys_present(self, env_file: Path):
        _write(env_file, "db.host=localhost\n")
        assert _run_flatten(_args(str(env_file))) == 1

    def test_missing_file_exits_two(self, tmp_path: Path):
        missing = str(tmp_path / "ghost.env")
        assert _run_flatten(_args(missing)) == 2

    def test_in_place_writes_flattened_content(self, env_file: Path):
        _write(env_file, "db.host=localhost\ndb.port=5432\n")
        _run_flatten(_args(str(env_file), in_place=True))
        content = env_file.read_text(encoding="utf-8")
        assert "DB_HOST=localhost" in content
        assert "DB_PORT=5432" in content
        assert "db.host" not in content

    def test_in_place_no_change_leaves_file_intact(self, env_file: Path):
        original = "FOO=bar\n"
        _write(env_file, original)
        _run_flatten(_args(str(env_file), in_place=True))
        # file should not be rewritten when there are no changes
        assert env_file.read_text(encoding="utf-8") == original

    def test_custom_separators_applied(self, env_file: Path):
        _write(env_file, "db__host=localhost\n")
        rc = _run_flatten(_args(str(env_file), from_sep="__", to_sep="_", in_place=True))
        assert rc == 1
        content = env_file.read_text(encoding="utf-8")
        assert "DB_HOST=localhost" in content

    def test_no_uppercase_preserves_case(self, env_file: Path, capsys):
        _write(env_file, "db.host=localhost\n")
        _run_flatten(_args(str(env_file), no_uppercase=True))
        captured = capsys.readouterr()
        assert "db_host=localhost" in captured.out
