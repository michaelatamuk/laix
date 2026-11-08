"""Run the deterministic prototype benchmark for the four algorithm directions."""

from __future__ import annotations

import json
from pathlib import Path

from laix import (
    ActionOption,
    AttentionCandidate,
    AttentionScheduler,
    CAVODPlanner,
    Commitment,
    ContinuityRecord,
    DecisionRequest,
    HumanAttentionBudget,
    LiveCompositePlanner,
    ObservationProbability,
    PlannerInput,
    PlannerPolicy,
    PomdpModel,
    PomdpTransition,
    WhittleCandidate,
    WhittleScheduler,
    WhittleTransition,
    counterfactual_attribution,
    decide,
    repair_continuity,
    whittle_index,
)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results" / "algorithm-directions" / "summary.json"


def _case(name: str, options: tuple[ActionOption, ...], attributes: dict) -> PlannerInput:
    return PlannerInput(
        subject=name,
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes=attributes,
    )


def _row(name: str, result) -> dict:
    return {
        "case": name,
        "action_id": result.action_id,
        "verb": result.verb,
        "reason_code": result.reason_code,
        "score": result.score,
        "information_value": (result.attributes or {}).get("information_value"),
        "option_value": (result.attributes or {}).get("option_value"),
        "future_value": (result.attributes or {}).get("future_value"),
    }


def ca_vod_cases() -> list[dict]:
    cases = (
        _case(
            "payment-approval",
            (
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
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
            ),
            {
                "commitments": (
                    Commitment(
                        id="c1",
                        subject="ask before paying",
                        due="2026-11-01T09:00:00+00:00",
                    ),
                ),
                "human_attention_budget": HumanAttentionBudget(total=2.0, spent=0.5),
                "uncertainty": 0.9,
            },
        ),
        _case(
            "uncertain-verification",
            (
                ActionOption(id="act", verb="act", name="act", expected_benefit=0.55, risk=0.2),
                ActionOption(id="verify", verb="verify", name="verify", expected_benefit=0.4),
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.3),
            ),
            {"uncertainty": 0.95},
        ),
        _case(
            "wait-option",
            (
                ActionOption(id="act", verb="act", name="act", expected_benefit=0.4, risk=0.5),
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
            ),
            {"uncertainty": 0.9},
        ),
    )
    rows = []
    for problem in cases:
        rows.append(
            {
                "live": _row(problem.subject, LiveCompositePlanner().solve(problem)),
                "ca_vod": _row(problem.subject, CAVODPlanner().solve(problem)),
            }
        )
    return rows


def ca_vod_belief_result() -> dict:
    model = PomdpModel(
        states=("safe", "risky"),
        actions=("act", "ask", "wait"),
        observations=("ok", "good", "bad"),
        transitions=(
            PomdpTransition(state="safe", action="act", next_state="safe", reward=1.0),
            PomdpTransition(state="risky", action="act", next_state="risky", reward=-1.0),
            PomdpTransition(state="safe", action="ask", next_state="safe"),
            PomdpTransition(state="risky", action="ask", next_state="risky"),
            PomdpTransition(state="safe", action="wait", next_state="safe"),
            PomdpTransition(state="risky", action="wait", next_state="risky"),
        ),
        observation_table=(
            ObservationProbability(next_state="safe", action="act", observation="ok"),
            ObservationProbability(next_state="risky", action="act", observation="ok"),
            ObservationProbability(next_state="safe", action="ask", observation="good"),
            ObservationProbability(next_state="risky", action="ask", observation="bad"),
            ObservationProbability(next_state="safe", action="wait", observation="ok"),
            ObservationProbability(next_state="risky", action="wait", observation="ok"),
        ),
        discount=0.9,
        horizon=2,
    )
    problem = PlannerInput(
        subject="belief",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.55),
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.2),
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
        ),
        attributes={},
    )
    one_step = CAVODPlanner().solve(problem)
    with_belief = CAVODPlanner(
        pomdp_model=model,
        belief={"safe": 0.5, "risky": 0.5},
    ).solve(problem)
    return {
        "one_step": _row(problem.subject, one_step),
        "belief": _row(problem.subject, with_belief),
    }


def aads_result() -> dict:
    schedule = AttentionScheduler().schedule(
        (
            AttentionCandidate(
                id="refund-approval",
                risk=0.9,
                commitment=True,
                information_value=0.4,
                deadline="2026-11-01T10:05:00+00:00",
            ),
            AttentionCandidate(
                id="routine-review",
                risk=0.2,
                deadline="2026-11-01T12:00:00+00:00",
            ),
            AttentionCandidate(
                id="check-evidence",
                risk=0.4,
                information_value=0.6,
                review_cost=0.5,
            ),
        ),
        now="2026-11-01T10:00:00+00:00",
        budget=1.5,
    )
    return {
        "selected": [row.candidate_id for row in schedule.selected],
        "deferred": [row.candidate_id for row in schedule.deferred],
        "spent": schedule.spent,
        "budget": schedule.budget,
    }


def aads_whittle_result() -> dict:
    def candidate(candidate_id: str, reward: float) -> WhittleCandidate:
        return WhittleCandidate(
            id=candidate_id,
            states=("bad", "good"),
            start="bad",
            active_transitions=(
                WhittleTransition(state="bad", next_state="good"),
                WhittleTransition(state="good", next_state="good"),
            ),
            passive_transitions=(
                WhittleTransition(state="bad", next_state="bad"),
                WhittleTransition(state="good", next_state="good"),
            ),
            active_reward={"bad": reward, "good": 0.2},
            passive_reward={"bad": 0.0, "good": 0.0},
            active_cost=0.1,
            review_cost=1.0,
            discount=0.9,
        )

    high = candidate("high", 1.0)
    low = candidate("low", 0.1)
    schedule = WhittleScheduler().schedule((low, high), budget=1.0)
    return {
        "indices": {
            "high": whittle_index(high),
            "low": whittle_index(low),
        },
        "selected": [row.candidate_id for row in schedule.selected],
        "deferred": [row.candidate_id for row in schedule.deferred],
        "spent": schedule.spent,
        "budget": schedule.budget,
    }


def cdr_result() -> dict:
    plan = repair_continuity(
        (
            ContinuityRecord(
                id="approval-1",
                kind="approval",
                status="rejected",
                refs=("order-1",),
                cost=1.0,
            ),
            ContinuityRecord(
                id="receipt-1",
                kind="receipt",
                status="executed",
                refs=("order-1",),
                cost=3.0,
            ),
        )
    )
    return {
        "conflicts": plan.conflicts,
        "actions": [
            {
                "record_id": action.record_id,
                "action": action.action,
                "to_status": action.to_status,
                "cost": action.cost,
            }
            for action in plan.actions
        ],
        "total_cost": plan.total_cost,
        "consistent": plan.consistent,
    }


def cda_result() -> dict:
    request = DecisionRequest(
        subject="invoice 4832",
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
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
        ),
        attributes={
            "commitments": (
                Commitment(
                    id="c1",
                    subject="ask before paying",
                    due="2026-11-01T09:00:00+00:00",
                ),
            ),
            "human_attention_budget": HumanAttentionBudget(total=2.0, spent=0.5),
            "uncertainty": 0.8,
        },
    )
    decision = decide(
        request,
        policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"),
    )[0]
    report = counterfactual_attribution(decision)
    minimal = report.minimal
    return {
        "chosen_id": report.chosen_id,
        "minimal": None
        if minimal is None
        else {
            "alternative_id": minimal.alternative_id,
            "component": minimal.component,
            "delta": minimal.delta,
            "explanation": minimal.explanation,
        },
        "counterfactual_count": len(report.counterfactuals),
    }


def main() -> int:
    payload = {
        "generated_by": "scripts/novelty/bench/run_algorithm_bench.py",
        "status": "prototype",
        "ca_vod": ca_vod_cases(),
        "ca_vod_belief": ca_vod_belief_result(),
        "aads": aads_result(),
        "aads_whittle": aads_whittle_result(),
        "cdr": cdr_result(),
        "cda": cda_result(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
