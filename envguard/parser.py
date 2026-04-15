"""Parser for .env files — reads and returns key-value pairs."""

import re
from pathlib import Path
from typing import Dict, Optional


ENV_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)\s*$"
)
COMMENT_RE = re.compile(r"^\s*#")


def parse_env_file(path: str | Path) -> Dict[str, Optional[str]]:
    """Parse a .env file and return a dict of key -> value.

    - Blank lines and comments (lines starting with #) are ignored.
    - Values may be optionally quoted with single or double quotes;
      surrounding quotes are stripped.
    - A key with no value (e.g. ``KEY=``) maps to an empty string.

    Args:
        path: Path to the .env file.

    Returns:
        Ordered dict mapping variable names to their string values.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file contains a malformed line.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")

    result: Dict[str, Optional[str]] = {}

    with path.open(encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")

            # Skip blanks and comments
            if not line.strip() or COMMENT_RE.match(line):
                continue

            match = ENV_LINE_RE.match(line)
            if not match:
                raise ValueError(
                    f"Malformed line {lineno} in {path}: {line!r}"
                )

            key = match.group("key")
            value = match.group("value").strip()

            # Strip matching surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]

            result[key] = value

    return result
