"""One forward action and its optional compensation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

Forward = Callable[[], dict]
Compensate = Callable[[], dict]


@dataclass(frozen=True, slots=True)
class SagaStep:
    """One forward action and its optional compensation."""

    name: str
    forward: Forward
    compensate: Compensate | None = None


__all__ = ["SagaStep"]
