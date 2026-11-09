"""The outcome of one execution saga."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SagaResult:
    completed: tuple[str, ...]
    compensated: tuple[str, ...]
    error: str | None = None


__all__ = ["SagaResult"]
