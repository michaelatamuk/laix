"""A small declarative policy: rules over request attributes."""

from __future__ import annotations

from typing import Any, Iterable

from ......decisions import Decision
from .rule import Rule


def _matches(attributes: dict[str, Any], when: dict[str, Any]) -> bool:
    for key, expected in when.items():
        actual = attributes.get(key)
        if isinstance(expected, dict):
            for operator, value in expected.items():
                if operator == "gte" and not (actual is not None and actual >= value):
                    return False
                if operator == "lte" and not (actual is not None and actual <= value):
                    return False
                if operator == "in" and actual not in value:
                    return False
                if operator == "contains" and (actual is None or value not in actual):
                    return False
                if operator not in {"gte", "lte", "in", "contains"}:
                    return False
        elif actual != expected:
            return False
    return True


class RulePolicy:
    """A deterministic policy authored as a list of ``Rule`` objects."""

    def __init__(
        self,
        rules: Iterable[Rule],
        *,
        name: str = "rules.v1",
        fallback: Rule | None = None,
    ) -> None:
        self.rules = tuple(rules)
        self.name = name
        self.version = name
        self.fallback = fallback or Rule(
            when={},
            verb="wait",
            reason_code="no_rule",
            rationale="no rule matched",
            confidence=0.5,
        )

    def decide(self, request: Any) -> list[Decision]:
        attributes = dict(getattr(request, "attributes", {}) or {})
        for rule in self.rules:
            if _matches(attributes, rule.when):
                return [self._decision(rule)]
        return [self._decision(self.fallback)]

    def _decision(self, rule: Rule) -> Decision:
        return Decision(
            verb=rule.verb,
            confidence=rule.confidence,
            reason_code=rule.reason_code,
            rationale=rule.rationale or rule.reason_code,
            action_id=rule.action_id,
            intent=rule.intent,
            requires_approval=rule.requires_approval,
            policy_version=self.name,
        )


__all__ = ["Rule", "RulePolicy"]
