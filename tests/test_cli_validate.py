"""Integration tests for the `envguard validate` CLI command."""

import json
import pytest
from pathlib import Path
from envguard.cli import main


@pytest.fixture
def env_file(tmp_path):
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(content)
        return str(p)
    return _write


def test_validate_clean_file_exits_zero(env_file):
    path = env_file("HOST=localhost\nPORT=8080\n")
    assert main(["validate", path]) == 0


def test_validate_missing_required_key_exits_one(env_file):
    path = env_file("HOST=localhost\n")
    assert main(["validate", path, "--require", "HOST", "PORT"]) == 1


def test_validate_all_required_present_exits_zero(env_file):
    path = env_file("HOST=localhost\nPORT=8080\n")
    assert main(["validate", path, "--require", "HOST", "PORT"]) == 0


def test_validate_bad_port_pattern_exits_one(env_file):
    path = env_file("PORT=not-a-port\n")
    assert main(["validate", path, "--pattern", "PORT=port"]) == 1


def test_validate_good_url_pattern_exits_zero(env_file):
    path = env_file("DATABASE_URL=https://db.host.com/mydb\n")
    assert main(["validate", path, "--pattern", "DATABASE_URL=url"]) == 0


def test_validate_empty_value_warning_still_exits_zero(env_file, capsys):
    path = env_file("SECRET=\n")
    code = main(["validate", path])
    assert code == 0  # warnings don't make it invalid
    captured = capsys.readouterr()
    assert "WARNING" in captured.out


def test_validate_allow_empty_suppresses_warning(env_file, capsys):
    path = env_file("SECRET=\n")
    main(["validate", path, "--allow-empty"])
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out


def test_validate_json_output_structure(env_file, capsys):
    path = env_file("HOST=localhost\n")
    code = main(["validate", path, "--require", "HOST", "MISSING", "--format", "json"])
    assert code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is False
    assert any("MISSING" in e for e in data["errors"])
    assert "warnings" in data


def test_validate_json_output_valid(env_file, capsys):
    path = env_file("HOST=localhost\n")
    main(["validate", path, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True
    assert data["errors"] == []
