"""Run a policy offline, or shadow it against another without changing the answer."""

from __future__ import annotations

from typing import Any, Iterable

from ...decisions import Decision
from .shadow_difference import ShadowDifference


def _signature(decisions: Iterable[Decision]) -> tuple[tuple[str, str | None, str], ...]:
    return tuple((item.verb, item.action_id, item.reason_code) for item in decisions)


def simulate(policy: Any, requests: Iterable[Any]) -> list[list[Decision]]:
    """Run a policy over recorded requests; no side effects."""
    return [list(policy.decide(request)) for request in requests]


class ShadowPolicy:
    """Return the primary decision and record every disagreement."""

    def __init__(self, primary: Any, shadow: Any, *, name: str = "shadow.v1") -> None:
        self.primary = primary
        self.shadow = shadow
        self.name = name
        self.version = name
        self.differences: list[ShadowDifference] = []

    def decide(self, request: Any) -> list[Decision]:
        primary = list(self.primary.decide(request))
        shadow = list(self.shadow.decide(request))
        if _signature(primary) != _signature(shadow):
            self.differences.append(
                ShadowDifference(request=request, primary=tuple(primary), shadow=tuple(shadow))
            )
        return primary


__all__ = ["ShadowDifference", "ShadowPolicy", "simulate"]
