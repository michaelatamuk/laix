from __future__ import annotations

from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    DecisionScenario,
    DecisionStep,
    HumanAttentionBudget,
    ReplanPlanner,
    RolloutPlanner,
    plan_decisions,
    replan_decisions,
    rollout_decisions,
)


def _scenario() -> DecisionScenario:
    return DecisionScenario(
        steps=(
            DecisionStep(
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="pay",
                        verb="act",
                        name="pay",
                        expected_benefit=0.95,
                        risk=0.05,
                        requires_approval=True,
                        reversible=False,
                        interrupt_cost=0.6,
                        params={"commitments": {"violates": ["c1"]}},
                    ),
                    ActionOption(
                        id="ask",
                        verb="ask",
                        name="ask",
                        expected_benefit=0.6,
                        interrupt_cost=0.2,
                        params={"commitments": {"fulfills": ["c1"]}},
                    ),
                ),
            ),
            DecisionStep(
                at="2026-11-01T11:00:00+00:00",
                options=(
                    ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
                    ActionOption(id="verify", verb="verify", name="verify", expected_benefit=0.4),
                ),
            ),
        ),
        commitments=(
            Commitment(
                id="c1",
                subject="ask before paying",
                due="2026-11-01T09:00:00+00:00",
            ),
        ),
        human_attention_budget=HumanAttentionBudget(total=2.0, spent=0.5),
    )


def _greedy_trap() -> DecisionScenario:
    return DecisionScenario(
        steps=(
            DecisionStep(
                at="2026-11-01T10:00:00+00:00",
                options=(ActionOption(id="start", verb="wait", name="start", expected_benefit=0.0),),
            ),
            DecisionStep(
                at="2026-11-01T10:10:00+00:00",
                options=(
                    ActionOption(id="big", verb="act", name="big", expected_benefit=1.0, interrupt_cost=0.9),
                    ActionOption(id="small", verb="act", name="small", expected_benefit=0.6, interrupt_cost=0.3),
                ),
            ),
            DecisionStep(
                at="2026-11-01T10:20:00+00:00",
                options=(
                    ActionOption(id="bonus", verb="act", name="bonus", expected_benefit=1.0, interrupt_cost=0.6),
                    ActionOption(id="nothing", verb="wait", name="nothing", expected_benefit=0.1),
                ),
            ),
        ),
        human_attention_budget=HumanAttentionBudget(total=1.0, spent=0.0),
    )


def test_cabb_keeps_the_commitment_first() -> None:
    plan = CABBPlanner().plan(_scenario())

    assert plan.actions[0] == "ask"
    assert len(plan.actions) == 2
    assert plan.violations == ()
    assert plan.attention_spent <= 1.5
    assert plan.nodes > 0
    assert plan.optimal is True


def test_evaluate_replays_the_optimal_plan() -> None:
    planner = CABBPlanner()
    plan = planner.plan(_scenario())
    replay = planner.evaluate(_scenario(), plan.actions)

    assert replay.score == plan.score
    assert replay.actions == plan.actions


def test_cabb_empty_scenario() -> None:
    plan = plan_decisions(DecisionScenario(steps=()))

    assert plan.actions == ()
    assert plan.score == 0.0
    assert plan.optimal is True


def test_rollout_matches_the_commitment_first_choice() -> None:
    plan = RolloutPlanner().plan(_scenario())

    assert plan.actions[0] == "ask"
    assert len(plan.actions) == 2
    assert plan.optimal is False


def test_rollout_empty_scenario() -> None:
    plan = rollout_decisions(DecisionScenario(steps=()))

    assert plan.actions == ()
    assert plan.score == 0.0


def test_replan_after_the_first_step() -> None:
    result = ReplanPlanner().replan(_scenario(), ("ask",))

    assert result.executed == ("ask",)
    assert result.actions == ("verify",)
    assert result.optimal is True
    assert result.reason.startswith("replanned")


def test_replan_with_nothing_left() -> None:
    result = replan_decisions(_scenario(), ("ask", "verify"))

    assert result.actions == ()
    assert result.reason == "nothing left to replan"


def test_cabb_beats_greedy_rollout_on_attention_tradeoff() -> None:
    exact = CABBPlanner().plan(_greedy_trap())
    greedy = RolloutPlanner().plan(_greedy_trap())

    assert exact.actions == ("start", "small", "bonus")
    assert greedy.actions == ("start", "big", "nothing")
    assert exact.score > greedy.score
