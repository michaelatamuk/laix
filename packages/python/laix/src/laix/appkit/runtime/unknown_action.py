"""Raised when a decision names an option the bridge cannot execute."""

from __future__ import annotations


class UnknownAction(RuntimeError):
    """Raised when a decision names an option the bridge cannot execute."""


__all__ = ["UnknownAction"]
