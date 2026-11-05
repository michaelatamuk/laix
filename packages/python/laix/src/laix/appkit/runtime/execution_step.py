"""One forward action and its optional compensation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ...core.decisions import ActionOption, Decision, ExecutionReceipt


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    """One forward action and its optional compensation."""

    action: ActionOption
    decision: Decision | None = None
    actor: str | None = None
    approver: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = None
    compensate: Callable[[ExecutionReceipt], dict[str, Any]] | None = None


__all__ = ["ExecutionStep"]
