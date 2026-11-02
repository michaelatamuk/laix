"""One deterministic bench case: a request and the fields it should produce."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class BenchCase:
    id: str
    request: Any
    expected: Mapping[str, Any]


__all__ = ["BenchCase"]
