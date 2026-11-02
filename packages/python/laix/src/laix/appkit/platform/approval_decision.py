"""What the platform or approver decided about a request."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approved: bool
    by: str = ""
    at: str = ""
    note: str = ""


__all__ = ["ApprovalDecision"]
