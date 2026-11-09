"""The compared result of one case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Row:
    case_id: str
    expected: tuple[Mapping[str, object], ...]
    actual: tuple[Mapping[str, object], ...]
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.mismatches


__all__ = ["Row"]
