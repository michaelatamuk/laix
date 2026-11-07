"""A small name-to-policy map used by ``DecisionClient``."""

from __future__ import annotations

from ...support.errors import DecisionPolicyError
from .decision_policy import DecisionPolicy


class DecisionPolicyRegistry:
    """A small name-to-policy map used by ``DecisionClient``."""

    def __init__(self) -> None:
        self._policies: dict[str, DecisionPolicy] = {}

    def register(self, name: str, policy: DecisionPolicy) -> None:
        key = name.strip()
        if not key:
            raise DecisionPolicyError("policy name is required")
        if not callable(getattr(policy, "decide", None)):
            raise DecisionPolicyError(f"policy {key!r} has no decide method")
        self._policies[key] = policy

    def get(self, name: str) -> DecisionPolicy:
        try:
            return self._policies[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._policies)) or "none"
            raise DecisionPolicyError(f"unknown policy {name!r}; registered: {known}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))


__all__ = ["DecisionPolicyRegistry"]
