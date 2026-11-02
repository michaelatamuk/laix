"""Raised when a destructive decision has no approver."""

from __future__ import annotations


class ApprovalRequired(RuntimeError):
    """Raised when a destructive decision has no approver."""


__all__ = ["ApprovalRequired"]
