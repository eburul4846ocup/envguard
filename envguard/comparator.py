"""Compare two parsed .env file dictionaries and report differences."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ComparisonResult:
    """Holds the result of comparing two .env files."""

    base_file: str
    target_file: str
    missing_in_target: List[str] = field(default_factory=list)
    missing_in_base: List[str] = field(default_factory=list)
    value_mismatches: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(
            self.missing_in_target or self.missing_in_base or self.value_mismatches
        )

    def summary(self) -> str:
        lines = [
            f"Comparing '{self.base_file}' (base) vs '{self.target_file}' (target)",
            "-" * 60,
        ]
        if not self.has_differences:
            lines.append("No differences found.")
            return "\n".join(lines)

        if self.missing_in_target:
            lines.append(f"Missing in target ({len(self.missing_in_target)}):")
            for key in sorted(self.missing_in_target):
                lines.append(f"  - {key}")

        if self.missing_in_base:
            lines.append(f"Extra in target / missing in base ({len(self.missing_in_base)}):")
            for key in sorted(self.missing_in_base):
                lines.append(f"  + {key}")

        if self.value_mismatches:
            lines.append(f"Value mismatches ({len(self.value_mismatches)}):")
            for key in sorted(self.value_mismatches):
                base_val = self.value_mismatches[key]["base"]
                target_val = self.value_mismatches[key]["target"]
                lines.append(f"  ~ {key}")
                lines.append(f"      base:   {base_val!r}")
                lines.append(f"      target: {target_val!r}")

        return "\n".join(lines)


def compare_envs(
    base: Dict[str, Optional[str]],
    target: Dict[str, Optional[str]],
    base_name: str = ".env.base",
    target_name: str = ".env.target",
    ignore_values: bool = False,
) -> ComparisonResult:
    """Compare two env dicts and return a ComparisonResult.

    Args:
        base: Parsed dict from the reference/base .env file.
        target: Parsed dict from the target .env file.
        base_name: Label for the base file (used in output).
        target_name: Label for the target file (used in output).
        ignore_values: When True, only check for key presence, not value equality.
    """
    result = ComparisonResult(base_file=base_name, target_file=target_name)

    base_keys = set(base.keys())
    target_keys = set(target.keys())

    result.missing_in_target = list(base_keys - target_keys)
    result.missing_in_base = list(target_keys - base_keys)

    if not ignore_values:
        for key in base_keys & target_keys:
            if base[key] != target[key]:
                result.value_mismatches[key] = {
                    "base": base[key],
                    "target": target[key],
                }

    return result
