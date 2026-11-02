"""One bench suite: a named decision class and its cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .case import BenchCase


@dataclass(frozen=True, slots=True)
class Suite:
    name: str
    description: str
    policy: Callable[[], Any]
    cases: tuple[BenchCase, ...]


__all__ = ["Suite"]
