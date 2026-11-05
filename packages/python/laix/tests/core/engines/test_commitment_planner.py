"""Commitment-aware planning: promises change the chosen option."""

from __future__ import annotations

import pytest

from laix import (
    ActionOption,
    Commitment,
    CommitmentAwareEngine,
    CommitmentWeights,
    DecisionProblem,
    UtilityEngine,
)


def _problem(*options: ActionOption, commitments: tuple[Commitment, ...] = ()) -> DecisionProblem:
    return DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes={"commitments": commitments},
    )


def _option(identifier: str, benefit: float, *, commitments: dict | None = None) -> ActionOption:
    return ActionOption(
        id=identifier,
        verb="act",
        name=identifier,
        expected_benefit=benefit,
        params={"commitments": commitments} if commitments else {},
    )


def test_violating_a_commitment_changes_the_choice() -> None:
    commitments = (Commitment(id="c1", subject="send the report", priority=1.0),)
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("send-now", 1.0, commitments={"violates": ["c1"]}),
            _option("send-later", 0.6, commitments={"fulfills": ["c1"]}),
            commitments=commitments,
        )
    )

    assert plan.verb == "act"
    assert plan.action_id == "send-later"
    assert plan.reason_code == "commitment_aware"
    assert plan.attributes["commitments_fulfilled"] == ["c1"]
    assert plan.attributes["commitments_violated"] == []


def test_due_commitment_gets_extra_weight() -> None:
    commitments = (
        Commitment(
            id="later",
            subject="not due",
            due="2026-11-02T09:00:00+00:00",
        ),
        Commitment(
            id="now",
            subject="due now",
            due="2026-11-01T09:00:00+00:00",
        ),
    )
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("do-later", 0.6, commitments={"fulfills": ["later"]}),
            _option("do-now", 0.6, commitments={"fulfills": ["now"]}),
            commitments=commitments,
        )
    )

    assert plan.action_id == "do-now"
    assert plan.attributes["commitments_due_fulfilled"] == ["now"]


def test_a_dependency_blocks_fulfillment() -> None:
    commitments = (
        Commitment(id="c0", subject="prerequisite"),
        Commitment(id="c1", subject="dependent", depends_on=("c0",)),
    )
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("do-c0", 0.5, commitments={"fulfills": ["c0"]}),
            _option("do-c1", 0.5, commitments={"fulfills": ["c1"]}),
            commitments=commitments,
        )
    )

    assert plan.action_id == "do-c0"
    assert plan.attributes["commitments_blocked_fulfilled"] == []


def test_a_done_dependency_unblocks_fulfillment() -> None:
    commitments = (
        Commitment(id="c0", subject="prerequisite", status="done"),
        Commitment(id="c1", subject="dependent", depends_on=("c0",)),
    )
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("do-c0", 0.5),
            _option("do-c1", 0.5, commitments={"fulfills": ["c1"]}),
            commitments=commitments,
        )
    )

    assert plan.action_id == "do-c1"


def test_priority_scales_the_reward() -> None:
    commitments = (
        Commitment(id="low", subject="low", priority=0.1),
        Commitment(id="high", subject="high", priority=1.0),
    )
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("do-low", 0.5, commitments={"fulfills": ["low"]}),
            _option("do-high", 0.5, commitments={"fulfills": ["high"]}),
            commitments=commitments,
        )
    )

    assert plan.action_id == "do-high"


def test_creating_a_commitment_costs_future_flexibility() -> None:
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("simple", 0.7),
            _option("promise-more", 0.7, commitments={"creates": ["c-new"]}),
        )
    )

    assert plan.action_id == "simple"
    assert plan.attributes["commitments_created"] == []


def test_hard_violation_blocks_an_option() -> None:
    commitments = (Commitment(id="c1", subject="do not break this"),)
    plan = CommitmentAwareEngine().solve(
        _problem(
            _option("break", 1.0, commitments={"violates": ["c1"], "hard": True}),
            _option("keep", 0.4, commitments={"fulfills": ["c1"]}),
            commitments=commitments,
        )
    )

    assert plan.action_id == "keep"
    alternatives = {row["action_id"]: row for row in plan.alternatives}
    assert "blocked by hard commitment" in alternatives["break"]["rejected_because"]


def test_no_commitments_matches_the_utility_engine() -> None:
    options = (
        ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
        ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
    )
    problem = _problem(*options)

    assert (
        CommitmentAwareEngine().solve(problem).action_id
        == UtilityEngine().solve(problem).action_id
    )


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError):
        CommitmentWeights(violate=-1.0)
