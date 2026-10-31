"""Policy plugins.

A policy is any object with a name and a ``decide`` method. It receives a
``DecisionRequest`` and returns decisions. The layer does not care how the policy
is implemented: rules, a learned model, a remote service or a test double.

A custom policy returns ``laix.layer.Decision``. The layer also accepts the core
or attention decision shapes and normalises them, so a policy can reuse the
existing contracts without rewriting them.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Policy(Protocol):
    """The smallest contract a policy plugin implements."""

    name: str

    def decide(self, request: Any) -> list[Any]:
        ...


class PolicyError(ValueError):
    """Raised when a policy name is unknown or a policy returns an invalid result."""


class PolicyRegistry:
    """A small name-to-policy map used by ``Layer``."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}

    def register(self, name: str, policy: Policy) -> None:
        key = name.strip()
        if not key:
            raise PolicyError("policy name is required")
        if not callable(getattr(policy, "decide", None)):
            raise PolicyError(f"policy {key!r} has no decide method")
        self._policies[key] = policy

    def get(self, name: str) -> Policy:
        try:
            return self._policies[name]
        except KeyError as exc:
            known = ", ".join(sorted(self._policies)) or "none"
            raise PolicyError(f"unknown policy {name!r}; registered: {known}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._policies))


__all__ = ["Policy", "PolicyError", "PolicyRegistry"]
