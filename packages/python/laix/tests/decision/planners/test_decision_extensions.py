"""Decision extensions: trust, resolution, portfolios and revalidation."""

from __future__ import annotations

from datetime import timedelta

from laix import (
    ActionOption,
    CAVODPlanner,
    CaseBasedPlanner,
    Commitment,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    CommitmentResolutionPlanner,
    ConflictResolutionPlanner,
    LiveCompositePlanner,
    MdpModel,
    MdpTransition,
    PastDecision,
    PlannerInput,
    PlannerResult,
    PortfolioPlanner,
    RevalidationPlanner,
    RiskBoundedPlanner,
    commitment_verification_counterfactual,
    policy_iteration,
)

SUPPLIER = CommitmentRef(owner="supplier", ledger="supplier", id="c2")


class _FixedPlanner:
    def __init__(self, action_id: str) -> None:
        self.action_id = action_id

    def solve(self, problem: PlannerInput) -> PlannerResult:
        return PlannerResult(
            verb="act",
            confidence=1.0,
            reason_code="fixed",
            rationale="fixed",
            action_id=self.action_id,
        )


def _graph(source: str = "reported", verified_at: str | None = None) -> CommitmentGraph:
    local = CommitmentLedger(
        (
            Commitment(
                id="deliver",
                subject="deliver",
                external_depends_on=(SUPPLIER,),
            ),
        )
    )
    external = Commitment(
        id="c2",
        subject="ship",
        owner="supplier",
        ledger="supplier",
        status="done",
        source=source,
        verified_at=verified_at,
    )
    return CommitmentGraph(local, (external,))


def _problem(graph: CommitmentGraph) -> PlannerInput:
    return PlannerInput(
        subject="deliver",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="finish",
                verb="act",
                name="finish",
                expected_benefit=1.0,
                params={"commitments": {"fulfills": ["deliver"], "hard": True}},
            ),
            ActionOption(
                id="wait",
                verb="wait",
                name="wait",
                expected_benefit=0.1,
            ),
        ),
        attributes={"commitment_graph": graph},
    )


def test_verified_without_timestamp_is_untrusted() -> None:
    commitment = Commitment(id="c", subject="s", source="verified")

    assert commitment.trusted is False
    assert _graph(source="verified").blocked(
        _graph(source="verified").local.get("deliver"),
        require_verified=True,
    )


def test_commitment_rejection_codes() -> None:
    commitments = CommitmentLedger((Commitment(id="c1", subject="keep"),))
    problem = PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="break",
                verb="act",
                name="break",
                params={"commitments": {"violates": ["c1"], "hard": True}},
            ),
            ActionOption(
                id="keep",
                verb="act",
                name="keep",
                params={"commitments": {"fulfills": ["c1"]}},
            ),
        ),
        attributes={"commitments": commitments},
    )
    plan = CommitmentPlanner().solve(problem)
    break_row = next(
        row for row in plan.alternatives if row["action_id"] == "break"
    )
    assert break_row["rejected_reason_code"] == "blocked_hard_commitment"

    stale = _graph(source="verified", verified_at="2026-10-01T09:00:00+00:00")
    plan = CommitmentPlanner(
        max_verification_age=timedelta(days=1)
    ).solve(_problem(stale))
    finish = next(row for row in plan.alternatives if row["action_id"] == "finish")
    assert finish["rejected_reason_code"] == "blocked_stale_dependency"


def test_resolution_planner_proposes_verification() -> None:
    plan = CommitmentResolutionPlanner().solve(_problem(_graph()))

    assert plan.verb == "verify"
    assert plan.reason_code == "commitment_resolution"
    assert plan.intent is not None
    assert plan.intent.capability == "verify_commitment"
    assert plan.attributes["verification_refs"][0]["id"] == "c2"

    asked = CommitmentResolutionPlanner(mode="ask").solve(_problem(_graph()))
    assert asked.verb == "ask"
    assert asked.requires_approval is True


def test_composite_and_cavod_see_external_blockers() -> None:
    problem = _problem(_graph())

    assert LiveCompositePlanner().solve(problem).action_id != "finish"
    assert CAVODPlanner().solve(problem).action_id != "finish"


def test_revalidation_holds_revises_and_escalates() -> None:
    problem = PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(ActionOption(id="a", verb="act", name="a"),),
    )
    held = RevalidationPlanner(_FixedPlanner("a")).solve(
        PlannerInput(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            options=problem.options,
            attributes={"previous_action_id": "a"},
        )
    )
    assert held.reason_code == "decision_held"
    assert held.action_id == "a"

    revised = RevalidationPlanner(_FixedPlanner("b")).solve(
        PlannerInput(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            options=problem.options,
            attributes={"previous_action_id": "a"},
        )
    )
    assert revised.reason_code == "decision_revised"
    assert revised.action_id == "b"


def test_portfolio_selects_a_planner() -> None:
    portfolio = PortfolioPlanner(
        {"a": _FixedPlanner("a"), "b": _FixedPlanner("b")},
        selector=lambda problem: str((problem.attributes or {}).get("planner", "a")),
    )
    result = portfolio.solve(
        PlannerInput(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            options=(ActionOption(id="a", verb="act", name="a"), ActionOption(id="b", verb="act", name="b")),
            attributes={"planner": "b"},
        )
    )
    assert result.action_id == "b"
    assert result.attributes["planner"] == "b"


def test_risk_bounded_planner_rejects_the_downside() -> None:
    problem = PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="safe",
                verb="act",
                name="safe",
                expected_benefit=0.6,
                params={"risk_bound": {"cvar_loss": 0.1}},
            ),
            ActionOption(
                id="risky",
                verb="act",
                name="risky",
                expected_benefit=1.0,
                params={"risk_bound": {"cvar_loss": 0.9}},
            ),
        ),
    )
    plan = RiskBoundedPlanner(max_loss=0.5).solve(problem)

    assert plan.action_id == "safe"
    assert plan.attributes["cvar_loss"] == 0.1
    risky = next(row for row in plan.alternatives if row["action_id"] == "risky")
    assert risky["rejected_reason_code"] == "risk_limit"


def test_case_based_planner_reuses_a_similar_case() -> None:
    planner = CaseBasedPlanner(
        (PastDecision(subject="send the report", action_id="send-now"),)
    )
    plan = planner.solve(
        PlannerInput(
            subject="send the report today",
            at="2026-11-01T10:00:00+00:00",
            options=(
                ActionOption(id="send-now", verb="act", name="send now"),
                ActionOption(id="send-later", verb="wait", name="send later"),
            ),
        )
    )

    assert plan.action_id == "send-now"
    assert plan.reason_code == "case_based"


def test_conflict_resolution_escalates_or_resolves() -> None:
    problem = PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(ActionOption(id="a", verb="act", name="a"),),
        attributes={
            "goal_conflicts": [
                {"id": "g1", "left": "speed", "right": "safety", "severity": 0.9}
            ]
        },
    )
    assert ConflictResolutionPlanner().solve(problem).verb == "escalate"

    resolving = PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="balanced",
                verb="act",
                name="balanced",
                params={"resolves": ["g1"]},
            ),
        ),
        attributes={"goal_conflicts": [{"id": "g1", "severity": 0.9}]},
    )
    plan = ConflictResolutionPlanner().solve(resolving)
    assert plan.action_id == "balanced"
    assert plan.reason_code == "goal_conflict_resolved"


def test_commitment_counterfactual_finds_the_verification() -> None:
    result = commitment_verification_counterfactual(
        _problem(_graph()), CommitmentPlanner()
    )

    assert result.base_action_id == "wait"
    assert [item.name for item in result.flips] == ["supplier/c2"]
    assert result.flips[0].counterfactual_action_id == "finish"


def test_policy_iteration_matches_the_discounted_model() -> None:
    model = MdpModel(
        states=("s0", "s1", "s2"),
        actions=("go", "stay"),
        transitions=(
            MdpTransition("s0", "go", "s1", 1.0, 1.0),
            MdpTransition("s0", "stay", "s0", 1.0, 0.0),
            MdpTransition("s1", "go", "s2", 1.0, 2.0),
            MdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        start="s0",
        discount=0.9,
        horizon=None,
    )
    result = policy_iteration(model)

    assert result.policy["s0"] == "go"
    assert result.policy["s1"] == "go"
    assert round(result.values["s0"], 6) == 2.8
