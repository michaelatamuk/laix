"""Outcome learning: labels become rewards, rewards change the choice."""

from __future__ import annotations

from laix import (
    Arm,
    BanditPolicy,
    DecisionRequest,
    DecisionClient,
    Outcome,
    UCBBandit,
    reward_for_label,
)


def outcome(decision_id: str, label: str) -> Outcome:
    return Outcome(
        id=f"o-{decision_id}-{label}",
        decision_id=decision_id,
        metric="success",
        before=0.0,
        after=1.0,
        delta=1.0,
        label=label,
        attributed=True,
        direction="higher-better",
    )


def test_labels_map_to_rewards() -> None:
    assert reward_for_label("helped") == 1.0
    assert reward_for_label("neutral") == 0.5
    assert reward_for_label("hurt") == 0.0
    assert reward_for_label("unknown") is None


def test_bandit_explores_then_prefers_the_rewarded_arm() -> None:
    bandit = UCBBandit([Arm("a"), Arm("b")])
    assert bandit.choose().id == "a"
    bandit.update("a", 0.0)
    bandit.update("b", 1.0)
    assert bandit.choose().id == "b"
    assert bandit.mean("b") > bandit.mean("a")


def test_bandit_respects_risk_and_budget() -> None:
    bandit = UCBBandit(
        [Arm("risky", risk=0.9), Arm("expensive", cost=9.0), Arm("safe", risk=0.1)]
    )
    chosen = bandit.choose(max_risk=0.2, budget=1.0)
    assert chosen is not None
    assert chosen.id == "safe"


def test_bandit_learns_from_labelled_outcomes() -> None:
    bandit = UCBBandit([Arm("a"), Arm("b")])
    used = bandit.learn(
        [outcome("d-1", "helped"), outcome("d-2", "hurt"), outcome("d-3", "unknown")],
        lambda decision_id: "a" if decision_id == "d-1" else "b",
    )
    assert used == 2
    assert bandit.pulls("a") == 1
    assert bandit.pulls("b") == 1
    assert bandit.mean("a") == 0.75
    assert bandit.mean("b") == 0.25


def test_bandit_policy_changes_its_choice_after_feedback() -> None:
    policy = BanditPolicy(UCBBandit([Arm("manual"), Arm("automatic")]))
    layer = DecisionClient(policy=policy)
    request = DecisionRequest(subject="pick a mode", at="2026-11-01T10:00:00+00:00")

    first = layer.decide(request)[0]
    assert first.action_id == "manual"

    policy.record("manual", 0.0)
    policy.record("automatic", 1.0)
    second = layer.decide(request)[0]

    assert second.action_id == "automatic"
    assert second.intent is not None
    assert second.intent.args["arm"] == "automatic"


def test_bandit_policy_waits_without_arms() -> None:
    decision = DecisionClient(policy=BanditPolicy()).decide(
        DecisionRequest(subject="pick", at="2026-11-01T10:00:00+00:00")
    )[0]
    assert decision.verb == "wait"
    assert decision.reason_code == "no_arms"
