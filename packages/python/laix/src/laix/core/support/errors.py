"""Errors shared by the decision layer and the policy registry."""

from __future__ import annotations


class PolicyError(ValueError):
    """Raised when a policy name is unknown or a policy returns an invalid result."""
