"""Stable, prefix-readable identifiers."""

from __future__ import annotations

import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def new_receipt_id() -> str:
    return new_id("RCT")


__all__ = ["new_id", "new_receipt_id"]
