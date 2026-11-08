"""Wrap a policy with the recipient target of its decisions."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from ......domain.decisions import Decision, TARGET_MODES


class TargetedPolicy:
    """Apply one target mode and recipient set to another policy's decisions."""

    name = "targeted.v1"

    def __init__(
        self,
        policy: Any,
        *,
        target: str = "request",
        recipients: Iterable[str] = (),
    ) -> None:
        if target != "request" and target not in TARGET_MODES:
            raise ValueError(f"unknown target mode: {target!r}")
        self.policy = policy
        self.target = target
        self.recipients = tuple(recipients)
        self.version = getattr(policy, "version", self.name)

    def decide(self, request: Any) -> list[Decision]:
        decisions = self.policy.decide(request)
        target = getattr(request, "target", "one") if self.target == "request" else self.target
        recipients = self.recipients or tuple(getattr(request, "recipients", ()) or ())
        return [
            replace(decision, target=target, recipients=recipients)
            for decision in decisions
        ]


__all__ = ["TargetedPolicy"]
