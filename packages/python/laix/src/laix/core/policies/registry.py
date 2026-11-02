"""A small name-to-policy map used by ``Layer``."""

from __future__ import annotations

from ..errors import PolicyError
from .policy import Policy


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


__all__ = ["PolicyRegistry"]
