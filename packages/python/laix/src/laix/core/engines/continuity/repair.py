"""Continuity decision repair (CDR).

A decision history can become inconsistent when a late receipt, a rejected
approval or a revised commitment contradicts an earlier record. This module
finds explicit and rule-derived conflicts and proposes a minimum-cost repair.

The full method is an incremental truth-maintenance system with a weighted
MaxSAT repair. This prototype is a deterministic greedy repair over the
cheapest side of each conflict.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


# (left kind, left status, right kind, right status)
DEFAULT_CONFLICT_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("approval", "rejected", "receipt", "executed"),
    ("commitment", "cancelled", "commitment", "done"),
    ("decision", "superseded", "decision", "final"),
)


@dataclass(frozen=True, slots=True)
class ContinuityRecord:
    """One record in the decision history."""

    id: str
    kind: str
    status: str
    refs: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    supports: tuple[str, ...] = ()
    cost: float = 1.0
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RepairAction:
    """One planned revision."""

    record_id: str
    action: str
    from_status: str
    to_status: str
    cost: float
    reason: str


@dataclass(frozen=True, slots=True)
class RepairPlan:
    """The conflicts found and the repair they imply."""

    conflicts: tuple[tuple[str, str], ...]
    actions: tuple[RepairAction, ...]
    total_cost: float
    consistent: bool


def _shared_refs(left: ContinuityRecord, right: ContinuityRecord) -> bool:
    return bool(set(left.refs) & set(right.refs))


def _matches(left: ContinuityRecord, right: ContinuityRecord, rule: tuple[str, str, str, str]) -> bool:
    left_kind, left_status, right_kind, right_status = rule
    return (
        left.kind == left_kind
        and left.status == left_status
        and right.kind == right_kind
        and right.status == right_status
    )


def _conflict_pairs(
    records: Sequence[ContinuityRecord],
    rules: Iterable[tuple[str, str, str, str]],
) -> list[tuple[ContinuityRecord, ContinuityRecord]]:
    by_id = {record.id: record for record in records}
    pairs: dict[tuple[str, str], tuple[ContinuityRecord, ContinuityRecord]] = {}

    for record in records:
        for other_id in record.conflicts:
            other = by_id.get(other_id)
            if other is None or other.id == record.id:
                continue
            key = tuple(sorted((record.id, other.id)))
            pairs[key] = (record, other)

    rules = tuple(rules)
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            if not _shared_refs(left, right):
                continue
            if any(_matches(left, right, rule) or _matches(right, left, rule) for rule in rules):
                key = tuple(sorted((left.id, right.id)))
                pairs.setdefault(key, (left, right))

    return list(pairs.values())


def repair_continuity(
    records: Sequence[ContinuityRecord],
    *,
    rules: Iterable[tuple[str, str, str, str]] = DEFAULT_CONFLICT_RULES,
) -> RepairPlan:
    """Find conflicts and supersede the cheapest side of each conflict."""
    conflicts = _conflict_pairs(records, rules)
    actions: list[RepairAction] = []

    for left, right in conflicts:
        if left.status == "superseded" or right.status == "superseded":
            continue
        if left.cost < right.cost:
            target, other = left, right
        elif right.cost < left.cost:
            target, other = right, left
        else:
            target, other = (left, right) if left.id > right.id else (right, left)
        actions.append(
            RepairAction(
                record_id=target.id,
                action="supersede",
                from_status=target.status,
                to_status="superseded",
                cost=round(max(0.0, float(target.cost)), 6),
                reason=f"conflicts with {other.id}",
            )
        )

    conflict_ids = tuple(
        tuple(sorted((left.id, right.id))) for left, right in conflicts
    )
    return RepairPlan(
        conflicts=conflict_ids,
        actions=tuple(actions),
        total_cost=round(sum(action.cost for action in actions), 6),
        consistent=not conflicts,
    )


__all__ = [
    "ContinuityRecord",
    "DEFAULT_CONFLICT_RULES",
    "RepairAction",
    "RepairPlan",
    "repair_continuity",
]
