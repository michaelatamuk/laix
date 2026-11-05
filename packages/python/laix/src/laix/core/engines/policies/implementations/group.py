"""Group decisions: target mode and private-state masking."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from ....decisions import Decision, TARGET_MODES


class GroupPolicy:
    """Apply a group target and remove private attributes before sharing."""

    name = "group.v1"

    def __init__(
        self,
        policy: Any,
        *,
        target: str = "some",
        recipients: Iterable[str] = (),
        private_attributes: Iterable[str] = (),
    ) -> None:
        if target not in TARGET_MODES:
            raise ValueError(f"unknown target mode: {target!r}")
        self.policy = policy
        self.target = target
        self.recipients = tuple(recipients)
        self.private_attributes = frozenset(private_attributes)
        self.version = getattr(policy, "version", self.name)

    def decide(self, request: Any) -> list[Decision]:
        recipients = self.recipients or tuple(getattr(request, "recipients", ()) or ())
        decisions = self.policy.decide(request)
        return [
            replace(
                decision,
                target=self.target,
                recipients=recipients,
                attributes={
                    key: value
                    for key, value in decision.attributes.items()
                    if key not in self.private_attributes
                },
            )
            for decision in decisions
        ]


__all__ = ["GroupPolicy"]
