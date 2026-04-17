"""Compare multiple .env files against a baseline."""
from __future__ import annotations

from pathlib import Path
from typing import List

from envguard.comparator import ComparisonResult, compare_envs
from envguard.parser import parse_env_file


def compare_many(
    baseline: Path,
    targets: List[Path],
    ignore_values: bool = False,
    ignore_extra: bool = False,
) -> List[ComparisonResult]:
    """Compare *baseline* against each file in *targets*."""
    base_vars = parse_env_file(baseline)
    results: List[ComparisonResult] = []
    for target in targets:
        target_vars = parse_env_file(target)
        result = compare_envs(
            base_vars,
            target_vars,
            source_name=str(baseline),
            target_name=str(target),
            ignore_values=ignore_values,
            ignore_extra=ignore_extra,
        )
        results.append(result)
    return results
