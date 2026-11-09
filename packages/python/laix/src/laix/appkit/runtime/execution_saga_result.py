"""The outcome of a multi-step execution, including every receipt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...decision.domain.decisions import ExecutionReceipt


@dataclass(frozen=True, slots=True)
class ExecutionSagaResult:
    """The outcome of a multi-step execution, including every receipt."""

    completed: tuple[str, ...]
    compensated: tuple[str, ...]
    receipts: tuple[ExecutionReceipt, ...]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": list(self.completed),
            "compensated": list(self.compensated),
            "receipts": [item.to_dict() for item in self.receipts],
            "error": self.error,
        }


__all__ = ["ExecutionSagaResult"]
