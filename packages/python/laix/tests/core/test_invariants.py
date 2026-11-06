"""Invariant tests for the formal model (formal-model.md §4).

Each test corresponds to one invariant I1–I10. These tests must keep
passing and must fail if the invariant is broken.

Run with:
    pytest tests/core/test_invariants.py -v
"""

from __future__ import annotations

import pytest

from laix import (
    ActionOption,
    AttentionBudget,
    CausalLedger,
    Commitment,
    Constraint,
    DecisionProblem,
    DecisionRequest,
    EnginePolicy,
    ExecutionReceipt,
    LiveDecisionEngine,
    Situation,
    UtilityEngine,
    decide,
)
from laix.core.decisions.trail.execution_receipt import EXECUTION_RECEIPT_STATUSES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AT = "2026-11-01T10:00:00+00:00"


def _problem(*options: ActionOption, **attributes: object) -> DecisionProblem:
    return DecisionProblem(
        subject="invariant case",
        at=AT,
        options=options,
        attributes=dict(attributes),
    )


def _option(
    id: str,
    *,
    benefit: float = 0.6,
    risk: float = 0.0,
    reversible: bool = True,
    interrupt_cost: float = 0.0,
    requires_approval: bool = False,
    verb: str = "act",
) -> ActionOption:
    return ActionOption(
        id=id,
        verb=verb,
        name=id,
        expected_benefit=benefit,
        risk=risk,
        reversible=reversible,
        interrupt_cost=interrupt_cost,
        requires_approval=requires_approval,
    )


# ---------------------------------------------------------------------------
# I1  Determinism
# ---------------------------------------------------------------------------


def test_i1_determinism() -> None:
    """I1: same problem + config → same plan every time."""
    problem = _problem(
        _option("a", benefit=0.9, risk=0.3),
        _option("b", benefit=0.6, risk=0.1),
        _option("c", benefit=0.7),
    )
    engine = LiveDecisionEngine()
    plan_1 = engine.solve(problem)
    plan_2 = engine.solve(problem)
    plan_3 = engine.solve(problem)

    assert plan_1.action_id == plan_2.action_id == plan_3.action_id
    assert plan_1.verb == plan_2.verb == plan_3.verb
    assert plan_1.score == plan_2.score == plan_3.score


# ---------------------------------------------------------------------------
# I2  Hard constraint gate
# ---------------------------------------------------------------------------


def test_i2_hard_constraint_gate_risk_limit() -> None:
    """I2: an option exceeding a hard risk constraint is never chosen."""
    risky = _option("risky", benefit=1.0, risk=0.6)
    safe = _option("safe", benefit=0.5, risk=0.1)

    situation = Situation(
        id="sit",
        at=AT,
        subject="risk limit",
        constraints=(Constraint(id="risk-limit", kind="risk", value=0.4, hard=True),),
    )
    # Pass situation as a DecisionProblem field, not via attributes.
    problem = DecisionProblem(
        subject="invariant case",
        at=AT,
        situation=situation,
        options=(risky, safe),
    )

    for engine in (UtilityEngine(), LiveDecisionEngine()):
        plan = engine.solve(problem)
        assert plan.action_id != "risky", (
            f"{engine.__class__.__name__} chose the risky option despite hard risk gate"
        )


def test_i2_hard_constraint_gate_blocks_all_options() -> None:
    """I2 edge: if all options exceed the hard limit, the planner waits."""
    risky_a = _option("a", benefit=1.0, risk=0.9)
    risky_b = _option("b", benefit=0.8, risk=0.8)

    situation = Situation(
        id="sit",
        at=AT,
        subject="risk limit",
        constraints=(Constraint(id="risk-limit", kind="risk", value=0.3, hard=True),),
    )
    problem = DecisionProblem(
        subject="invariant case",
        at=AT,
        situation=situation,
        options=(risky_a, risky_b),
    )
    plan = LiveDecisionEngine().solve(problem)

    assert plan.verb == "wait"


# ---------------------------------------------------------------------------
# I3  Attention budget
# ---------------------------------------------------------------------------


def test_i3_attention_budget_blocks_asking_when_exhausted() -> None:
    """I3: option that needs attention is blocked when the budget is spent."""
    ask = _option("ask", benefit=0.9, verb="ask")
    act = _option("act", benefit=0.6, verb="act")

    problem = _problem(
        ask,
        act,
        attention_budget=AttentionBudget(total=1.0, spent=1.0),
    )
    plan = LiveDecisionEngine().solve(problem)

    assert plan.action_id == "act", (
        "attention engine should choose act when budget is exhausted"
    )


def test_i3_attention_budget_allows_asking_when_budget_remains() -> None:
    """I3 inverse: option that needs attention is allowed when budget is available."""
    ask = _option("ask", benefit=0.9, verb="ask")
    act = _option("act", benefit=0.3, verb="act")

    problem = _problem(
        ask,
        act,
        attention_budget=AttentionBudget(total=1.0, spent=0.0),
    )
    plan = LiveDecisionEngine().solve(problem)

    assert plan.action_id == "ask"


# ---------------------------------------------------------------------------
# I4  Rejected approval
# ---------------------------------------------------------------------------


def test_i4_rejected_approval_never_chosen() -> None:
    """I4: an option with approval_state = rejected is never chosen."""
    rejected = _option("rejected", benefit=1.0)
    fallback = _option("fallback", benefit=0.4)

    problem = _problem(rejected, fallback, approvals={"rejected": "rejected"})
    plan = LiveDecisionEngine().solve(problem)

    assert plan.action_id == "fallback", (
        "rejected option must not be chosen regardless of utility"
    )


def test_i4_rejected_approval_all_rejected_waits() -> None:
    """I4 edge: if every option is rejected the planner waits."""
    opt_a = _option("a", benefit=0.9)
    opt_b = _option("b", benefit=0.8)

    problem = _problem(opt_a, opt_b, approvals={"a": "rejected", "b": "rejected"})
    plan = LiveDecisionEngine().solve(problem)

    assert plan.verb == "wait"


# ---------------------------------------------------------------------------
# I5  Revision monotonicity (DecisionTimeline)
# ---------------------------------------------------------------------------


def test_i5_revision_monotonicity_supersedes_must_exist() -> None:
    """I5: a revision that references a non-existent predecessor is rejected."""
    from laix import Decision, DecisionTimeline, TimelineError

    orphan = Decision(
        verb="guide",
        confidence=0.8,
        reason_code="stream",
        rationale="revision without predecessor",
        decision_id="DEC-orphan",
        revision=1,
        supersedes="DEC-does-not-exist",
        event_time="2026-11-01T10:00:00+00:00",
    )
    with pytest.raises(TimelineError):
        DecisionTimeline().add(orphan)


def test_i5_initial_revision_must_not_have_supersedes() -> None:
    """I5: a revision=0 decision must not reference a predecessor."""
    from laix import Decision, DecisionTimeline, TimelineError

    zero_with_supersedes = Decision(
        verb="guide",
        confidence=0.8,
        reason_code="stream",
        rationale="zero revision with supersedes",
        decision_id="DEC-zero",
        revision=0,
        supersedes="DEC-parent",
        event_time="2026-11-01T10:00:00+00:00",
    )
    with pytest.raises(TimelineError):
        DecisionTimeline().add(zero_with_supersedes)


# ---------------------------------------------------------------------------
# I6  Receipt state machine
# ---------------------------------------------------------------------------


def test_i6_valid_receipt_statuses_accepted() -> None:
    """I6: all documented statuses are accepted."""
    for status in EXECUTION_RECEIPT_STATUSES:
        receipt = ExecutionReceipt(
            id=f"REC-{status}",
            decision_id="DEC-1",
            action_name="pay",
            status=status,
            actor="system",
        )
        assert receipt.status == status


def test_i6_invalid_receipt_status_raises() -> None:
    """I6: an undocumented status is rejected at construction time."""
    with pytest.raises(ValueError, match="unknown receipt status"):
        ExecutionReceipt(
            id="REC-bad",
            decision_id="DEC-1",
            action_name="pay",
            status="invented_status",
            actor="system",
        )


# ---------------------------------------------------------------------------
# I7  Trace append-only
# ---------------------------------------------------------------------------


def test_i7_causal_ledger_append_only() -> None:
    """I7: CausalLedger.add never removes an existing entry."""
    ledger = CausalLedger()
    ledger.add("d1", arm="act", outcome=1.0)
    assert len(ledger.records) == 1

    ledger.add("d2", arm="wait", outcome=0.0)
    assert len(ledger.records) == 2

    ledger.add("d3", arm="act", outcome=0.5)
    assert len(ledger.records) == 3


def test_i7_causal_ledger_count_monotonically_increases() -> None:
    """I7: the count never decreases after an add."""
    ledger = CausalLedger()
    counts = []
    for i in range(10):
        ledger.add(f"d{i}", arm="act" if i % 2 == 0 else "wait", outcome=float(i % 2))
        counts.append(len(ledger.records))

    for i in range(1, len(counts)):
        assert counts[i] > counts[i - 1], "CausalLedger record count must monotonically increase"


# ---------------------------------------------------------------------------
# I8  Confidence bounds
# ---------------------------------------------------------------------------


def test_i8_confidence_bounds_all_planners() -> None:
    """I8: confidence ∈ [0.0, 1.0] for every planner on many problems."""
    from laix import (
        AttentionAwareEngine,
        CommitmentAwareEngine,
        ExecutionAwareEngine,
    )

    engines = [
        UtilityEngine(),
        CommitmentAwareEngine(),
        ExecutionAwareEngine(),
        AttentionAwareEngine(),
        LiveDecisionEngine(),
    ]
    problems = [
        _problem(),  # no options → wait
        _problem(_option("a", benefit=0.9)),
        _problem(_option("a", benefit=0.9), _option("b", benefit=0.1)),
        _problem(
            _option("a", benefit=0.9, risk=0.8),
            _option("b", benefit=0.5, risk=0.1),
        ),
        _problem(
            _option("a", benefit=0.9),
            _option("b", benefit=0.9),  # tie
        ),
    ]
    for engine in engines:
        for problem in problems:
            plan = engine.solve(problem)
            assert 0.0 <= plan.confidence <= 1.0, (
                f"{engine.__class__.__name__} returned confidence {plan.confidence!r} "
                f"outside [0, 1]"
            )


# ---------------------------------------------------------------------------
# I9  Contract consistency
# ---------------------------------------------------------------------------


def test_i9_contract_consistency_engine_policy_vs_decide() -> None:
    """I9: EnginePolicy(engine).decide(req) equals decide(req, policy=EnginePolicy(engine))."""
    request = DecisionRequest(
        subject="invoice",
        at=AT,
        options=(
            ActionOption(id="pay", verb="act", name="pay", expected_benefit=0.9),
            ActionOption(id="hold", verb="wait", name="hold", expected_benefit=0.5),
        ),
    )
    engine = UtilityEngine()
    policy = EnginePolicy(engine)

    via_policy = policy.decide(request)[0]
    via_decide = decide(request, policy=policy)[0]

    assert via_policy.verb == via_decide.verb
    assert via_policy.action_id == via_decide.action_id
    assert via_policy.reason_code == via_decide.reason_code
    assert via_policy.score == via_decide.score


# ---------------------------------------------------------------------------
# I10  Parity (Python/TypeScript)
# ---------------------------------------------------------------------------


def test_i10_parity_conformance_cases_exist() -> None:
    """I10: the conformance test suite exists and covers shared cases.

    Full Python/TypeScript parity is verified in tests/test_language_parity.py.
    This test checks that the conformance infrastructure is present so that I10
    remains part of the invariant suite.
    """
    from laix.core.schema import SCHEMA_PATH

    assert SCHEMA_PATH.exists(), (
        "conformance schema must exist for parity testing (I10)"
    )
