"""The compared result of one bench case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class BenchRow:
    suite: str
    case: str
    expected: Mapping[str, object]
    actual: Mapping[str, object]
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.mismatches


__all__ = ["BenchRow"]
