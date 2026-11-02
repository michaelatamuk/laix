"""One append-only audit event on a decision record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditEvent:
    at: str
    actor: str
    event: str
    detail: str = ""


__all__ = ["AuditEvent"]
