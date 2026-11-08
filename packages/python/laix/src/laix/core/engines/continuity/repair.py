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
    method: str = "greedy"


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


def _minimum_vertex_cover(
    pairs: Sequence[tuple[ContinuityRecord, ContinuityRecord]],
) -> set[str]:
    """Exact minimum-weight vertex cover by branch and bound."""
    if not pairs:
        return set()
    records = {record.id: record for pair in pairs for record in pair}
    edges = [frozenset((left.id, right.id)) for left, right in pairs]
    best: tuple[float, set[str]] = (float("inf"), set())

    def search(
        remaining: list[frozenset[str]],
        chosen: set[str],
        cost: float,
    ) -> None:
        nonlocal best
        if not remaining:
            if cost < best[0]:
                best = (cost, set(chosen))
            return
        if cost >= best[0]:
            return
        edge = max(
            remaining,
            key=lambda item: min(records[node].cost for node in item),
        )
        order = sorted(
            edge,
            key=lambda node: (records[node].cost, node),
        )
        for node in order:
            search(
                [item for item in remaining if node not in item],
                chosen | {node},
                cost + max(0.0, float(records[node].cost)),
            )

    search(edges, set(), 0.0)
    return best[1]


def repair_continuity(
    records: Sequence[ContinuityRecord],
    *,
    rules: Iterable[tuple[str, str, str, str]] = DEFAULT_CONFLICT_RULES,
    exact: bool = False,
) -> RepairPlan:
    """Find conflicts and repair them.

    The default is the greedy minimum-cost repair. Pass ``exact=True`` to solve
    the minimum-weight vertex cover by branch and bound.
    """
    conflicts = _conflict_pairs(records, rules)
    active = [
        (left, right)
        for left, right in conflicts
        if left.status != "superseded" and right.status != "superseded"
    ]
    actions: list[RepairAction] = []

    if exact:
        selected = _minimum_vertex_cover(active)
        for record_id in sorted(selected):
            record = next(item for item in records if item.id == record_id)
            actions.append(
                RepairAction(
                    record_id=record.id,
                    action="supersede",
                    from_status=record.status,
                    to_status="superseded",
                    cost=round(max(0.0, float(record.cost)), 6),
                    reason="minimum-weight vertex cover",
                )
            )
    else:
        for left, right in active:
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
        consistent=not active,
        method="exact" if exact else "greedy",
    )


__all__ = [
    "ContinuityRecord",
    "DEFAULT_CONFLICT_RULES",
    "RepairAction",
    "RepairPlan",
    "repair_continuity",
]
