"""Group decisions: target mode and private-state masking."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from ...domain.decisions import Decision, TARGET_MODES


class GroupPolicy:
    """Apply a group target and remove private data before sharing."""

    name = "group.v1"

    def __init__(
        self,
        policy: Any,
        *,
        target: str = "some",
        recipients: Iterable[str] = (),
        private_attributes: Iterable[str] = (),
        private_evidence: Iterable[str] = (),
        rationale: str | None = None,
        undo_hint: str | None = None,
    ) -> None:
        if target not in TARGET_MODES:
            raise ValueError(f"unknown target mode: {target!r}")
        self.policy = policy
        self.target = target
        self.recipients = tuple(recipients)
        self.private_attributes = frozenset(private_attributes)
        self.private_evidence = frozenset(private_evidence)
        self.rationale = rationale
        self.undo_hint = undo_hint
        self.version = getattr(policy, "version", self.name)

    def decide(self, request: Any) -> list[Decision]:
        recipients = self.recipients or tuple(getattr(request, "recipients", ()) or ())
        decisions = self.policy.decide(request)
        return [self._mask(decision, recipients) for decision in decisions]

    def _mask(self, decision: Decision, recipients: tuple[str, ...]) -> Decision:
        evidence = tuple(
            item
            for item in decision.evidence
            if not ({item.id, item.kind, item.source or ""} & self.private_evidence)
        )
        intent = decision.intent
        if intent is not None:
            intent = replace(intent, args=self._mask_value(intent.args))
        return replace(
            decision,
            target=self.target,
            recipients=recipients,
            rationale=self.rationale if self.rationale is not None else decision.rationale,
            undo_hint=self.undo_hint if self.undo_hint is not None else decision.undo_hint,
            evidence=evidence,
            intent=intent,
            alternatives=tuple(self._mask_value(item) for item in decision.alternatives),
            attributes=self._mask_value(decision.attributes),
        )

    def _mask_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._mask_value(item)
                for key, item in value.items()
                if key not in self.private_attributes
            }
        if isinstance(value, list):
            return [self._mask_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self._mask_value(item) for item in value)
        return value


__all__ = ["GroupPolicy"]
