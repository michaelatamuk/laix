"""LAIX-Bench v0: run every decision class against deterministic cases.

The bench is a suite of cases, one policy per class and a report. It has no app
data, no network and no randomness. Run it as a module::

    python -m laix.appkit.bench
    python -m laix.appkit.bench --suite safety --json
    python -m laix.appkit.bench --fail-under 1.0
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from ...decision.sensing.signals import SignalContext, SignalFeedback, Signal
from ...decision.evaluation.bench.live_bench import run_live_bench
from ...decision.domain.decisions import ActionOption, Belief, DecisionRequest, Situation
from ...decision.policies import (
    ActivePerceptionPolicy,
    AllocationPolicy,
    EscalationPolicy,
    NegotiationPolicy,
    PreferenceElicitationPolicy,
    ReplanningPolicy,
    SafetyConstrainedPolicy,
    VerificationPolicy,
)
from ..decision_client import DecisionClient
from .case import BenchCase
from .planner_bench import run_planner_bench
from .report import BenchReport
from .row import BenchRow
from .suite import Suite

AT = "2026-11-01T10:00:00+00:00"


def _decision_dict(decision: Any) -> dict[str, Any]:
    if isinstance(decision, Mapping):
        return dict(decision)
    to_dict = getattr(decision, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    return {
        "verb": getattr(decision, "verb", None),
        "reason_code": getattr(decision, "reason_code", None),
        "action_id": getattr(decision, "action_id", None),
        "requires_approval": getattr(decision, "requires_approval", False),
    }


def _request(**attributes: Any) -> DecisionRequest:
    return DecisionRequest(subject="bench case", at=AT, attributes=attributes)


def _attention(signal: Signal, moment: datetime, **context: Any) -> DecisionRequest:
    return DecisionRequest(
        subject=signal.title or signal.id,
        at=AT,
        signals=(signal,),
        context=SignalContext(now=moment, **context),
    )


def _action(situation: Situation, options: Sequence[ActionOption]) -> DecisionRequest:
    return DecisionRequest(subject=situation.subject, at=AT, situation=situation, options=tuple(options))


def _belief(subject: str) -> Belief:
    return Belief(id="belief-1", proposition=subject, confidence=0.95)


def _bill_signal() -> Signal:
    return Signal(
        id="bill-1",
        kind="deadline",
        title="Electricity bill due tomorrow",
        severity="high",
        confidence=0.95,
        due="2026-11-02T09:00:00+00:00",
    )


def _attention_suite() -> Suite:
    signal = _bill_signal()
    morning = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    night = datetime(2026, 11, 1, 23, 30, tzinfo=timezone.utc)
    return Suite(
        name="attention",
        description="which signal deserves attention now",
        policy=DecisionClient,
        cases=(
            BenchCase("attention_bill_day", _attention(signal, morning, quiet_hours=("22:00", "06:00")), {"verb": "guide", "reason_code": "worth_surfacing"}),
            BenchCase("signal_attention_quiet_hours", _attention(signal, night, quiet_hours=("22:00", "06:00")), {"verb": "wait", "reason_code": "quiet_hours"}),
            BenchCase(
                "attention_dismissed",
                _attention(signal, morning, quiet_hours=None, feedback={"bill-1": SignalFeedback(state="dismissed")}),
                {"verb": "wait", "reason_code": "dismissed"},
            ),
        ),
    )


def _action_suite() -> Suite:
    sink = Situation(
        id="sink-1",
        at=AT,
        subject="kitchen sink",
        beliefs=(_belief("the sink is about to overflow"),),
        attributes={"urgency": 0.9},
    )
    sink_options = (
        ActionOption(id="option-wait", verb="wait", name="keep watching", expected_benefit=0.1),
        ActionOption(id="option-close-valve", verb="act", name="close the valve", expected_benefit=0.95, risk=0.05, reversible=True),
    )
    payment = Situation(
        id="payment-1",
        at=AT,
        subject="electricity bill payment",
        beliefs=(_belief("the bill is due today"),),
        attributes={"urgency": 0.9},
    )
    payment_options = (
        ActionOption(id="option-wait", verb="wait", name="pay later", expected_benefit=0.1),
        ActionOption(id="option-pay", verb="act", name="pay the bill", expected_benefit=0.9, requires_approval=True),
    )
    parcel = Situation(
        id="parcel-1",
        at=AT,
        subject="late parcel",
        beliefs=(Belief(id="late", proposition="the parcel is late", confidence=0.6),),
        attributes={"urgency": 0.8, "needs_more_info": True},
    )
    parcel_options = (
        ActionOption(id="option-wait", verb="wait", name="keep waiting", expected_benefit=0.2),
        ActionOption(id="option-check-tracking", verb="observe", name="read the tracking page", expected_benefit=0.6),
        ActionOption(id="option-ask-courier", verb="ask", name="ask the courier", expected_benefit=0.4),
    )
    return Suite(
        name="action",
        description="which available action to take",
        policy=DecisionClient,
        cases=(
            BenchCase("action_sink", _action(sink, sink_options), {"verb": "act", "reason_code": "policy_rule", "action_id": "option-close-valve"}),
            BenchCase(
                "action_payment_approval",
                _action(payment, payment_options),
                {"verb": "act", "reason_code": "policy_rule", "action_id": "option-pay", "requires_approval": True},
            ),
            BenchCase(
                "action_check_first",
                _action(parcel, parcel_options),
                {"verb": "observe", "reason_code": "policy_rule", "action_id": "option-check-tracking"},
            ),
        ),
    )


def _active_perception_suite() -> Suite:
    return Suite(
        name="active-perception",
        description="look before deciding when uncertainty is high",
        policy=ActivePerceptionPolicy,
        cases=(
            BenchCase(
                "active_perception_look",
                _request(uncertainty=0.8, observations=[{"id": "look-1", "information_gain": 0.7, "cost": 0.1}]),
                {"verb": "observe", "reason_code": "observe_for_information", "action_id": "look-1"},
            ),
            BenchCase("active_perception_skip", _request(uncertainty=0.1), {"verb": "wait", "reason_code": "uncertainty_low"}),
        ),
    )


def _safety_suite() -> Suite:
    return Suite(
        name="safety",
        description="act only inside the hard risk limit",
        policy=SafetyConstrainedPolicy,
        cases=(
            BenchCase(
                "safety_safe_option",
                _request(risk_limit=0.2, options=[{"id": "valve", "benefit": 0.9, "risk": 0.1}, {"id": "hit-pipe", "benefit": 1.0, "risk": 0.9}]),
                {"verb": "act", "reason_code": "safe_action", "action_id": "valve"},
            ),
            BenchCase(
                "safety_blocked",
                _request(risk_limit=0.1, options=[{"id": "risky", "benefit": 1.0, "risk": 0.9}]),
                {"verb": "wait", "reason_code": "no_safe_option"},
            ),
        ),
    )


def _replanning_suite() -> Suite:
    plans = [
        {"id": "plan-slow", "success_probability": 0.95, "cost": 10, "deadline_risk": 0.1},
        {"id": "plan-fast", "success_probability": 0.8, "cost": 1, "deadline_risk": 0.1},
    ]
    return Suite(
        name="replanning",
        description="choose a replacement plan after the old one broke",
        policy=ReplanningPolicy,
        cases=(
            BenchCase("replanning_feasible", _request(plans=plans, min_success=0.7, max_cost=5), {"verb": "act", "reason_code": "replan", "action_id": "plan-fast"}),
            BenchCase("replanning_none", _request(plans=plans, min_success=0.99, max_cost=2), {"verb": "ask", "reason_code": "no_feasible_plan"}),
        ),
    )


def _allocation_suite() -> Suite:
    requests = [
        {"id": "a", "value": 6, "cost": 4},
        {"id": "b", "value": 5, "cost": 6},
        {"id": "c", "value": 9, "cost": 20},
    ]
    return Suite(
        name="allocation",
        description="fund a portfolio under a budget",
        policy=AllocationPolicy,
        cases=(
            BenchCase("allocation_fund", _request(budget=10, requests=requests), {"verb": "act", "reason_code": "allocate"}),
            BenchCase("allocation_empty", _request(budget=1, requests=requests), {"verb": "wait", "reason_code": "nothing_affordable"}),
        ),
    )


def _negotiation_suite() -> Suite:
    return Suite(
        name="negotiation",
        description="accept, counter or escalate an offer",
        policy=NegotiationPolicy,
        cases=(
            BenchCase("negotiation_counter", _request(offer=5, reservation=10, target=20, round=1), {"verb": "act", "reason_code": "counter_offer", "action_id": "counter_offer"}),
            BenchCase("negotiation_accept", _request(offer=12, reservation=10, target=20, round=1), {"verb": "act", "reason_code": "accept_offer", "action_id": "accept_offer"}),
            BenchCase("negotiation_round_limit", _request(offer=5, reservation=10, target=20, round=5), {"verb": "escalate", "reason_code": "round_limit"}),
        ),
    )


def _preference_suite() -> Suite:
    questions = [{"id": "q1", "information_gain": 0.2, "cost": 1}, {"id": "q2", "information_gain": 0.8, "cost": 1}]
    return Suite(
        name="preference",
        description="ask the question that reduces preference uncertainty most",
        policy=PreferenceElicitationPolicy,
        cases=(
            BenchCase("preference_ask", _request(uncertainty=0.8, questions=questions), {"verb": "ask", "reason_code": "ask_preference", "action_id": "q2"}),
            BenchCase("preference_known", _request(uncertainty=0.1, questions=questions), {"verb": "act", "reason_code": "preference_known"}),
        ),
    )


def _verification_suite() -> Suite:
    checks = [{"id": "manual", "confidence_gain": 0.2, "cost": 1}, {"id": "api", "confidence_gain": 0.8, "cost": 1}]
    return Suite(
        name="verification",
        description="confirm that an action did what it claimed",
        policy=VerificationPolicy,
        cases=(
            BenchCase("verification_check", _request(confidence=0.5, required_confidence=0.8, checks=checks), {"verb": "verify", "reason_code": "verify_outcome", "action_id": "api"}),
            BenchCase("verification_no_path", _request(confidence=0.3, required_confidence=0.8, checks=[]), {"verb": "escalate", "reason_code": "no_verification_path"}),
            BenchCase("verification_not_needed", _request(confidence=0.95, required_confidence=0.8, verification_due=False, checks=[]), {"verb": "wait", "reason_code": "verification_not_needed"}),
        ),
    )


def _escalation_suite() -> Suite:
    return Suite(
        name="escalation",
        description="decide when a situation must leave the current owner",
        policy=EscalationPolicy,
        cases=(
            BenchCase("escalation_target", _request(severity=0.9, severity_threshold=0.8, target="manager"), {"verb": "escalate", "reason_code": "escalate_to_target", "action_id": "manager"}),
            BenchCase("escalation_within_limits", _request(severity=0.2, severity_threshold=0.8, confidence=0.9), {"verb": "wait", "reason_code": "within_limits"}),
            BenchCase("escalation_target_required", _request(severity=0.9, severity_threshold=0.8), {"verb": "ask", "reason_code": "target_required"}),
        ),
    )


def all_suites() -> tuple[Suite, ...]:
    return (
        _attention_suite(),
        _action_suite(),
        _active_perception_suite(),
        _safety_suite(),
        _replanning_suite(),
        _allocation_suite(),
        _negotiation_suite(),
        _preference_suite(),
        _verification_suite(),
        _escalation_suite(),
    )


def suite_names() -> tuple[str, ...]:
    return tuple(suite.name for suite in all_suites())


def run_bench(suites: Sequence[str] | None = None) -> BenchReport:
    chosen = set(suites or ())
    selected = [suite for suite in all_suites() if not chosen or suite.name in chosen]
    rows: list[BenchRow] = []
    for suite in selected:
        policy = suite.policy()
        for case in suite.cases:
            decisions = policy.decide(case.request)
            decision = decisions[0] if decisions else {}
            actual = _decision_dict(decision)
            mismatches = tuple(
                f"{name}: {actual.get(name)!r} != {want!r}"
                for name, want in case.expected.items()
                if actual.get(name) != want
            )
            rows.append(BenchRow(suite.name, case.id, case.expected, actual, mismatches))
    return BenchReport(tuple(rows))


def _print_table(report: BenchReport) -> None:
    print(f"{'suite':24} {'cases':>6} {'passed':>7} {'agreement':>10}")
    print("-" * 51)
    for name, row in report.by_suite().items():
        print(f"{name:24} {row['cases']:>6} {row['passed']:>7} {row['agreement']:>10.3f}")
    print("-" * 51)
    print(f"{'overall':24} {report.total:>6} {report.passed:>7} {report.agreement:>10.3f}")
    failed = [row for row in report.rows if not row.passed]
    if failed:
        print()
        for row in failed:
            print(f"FAIL {row.suite}/{row.case}: {'; '.join(row.mismatches)}")


def _print_planner_table(report: Any) -> None:
    print(f"{'planner':24} {'scenario':20} {'reward':>8} {'steps':>6} {'gap':>8}")
    print("-" * 70)
    for row in report.rows:
        gap = "n/a" if row.optimality_gap is None else f"{row.optimality_gap:.3f}"
        print(
            f"{row.planner:24} {row.scenario:20} {row.total_reward:>8.3f} "
            f"{row.steps:>6} {gap:>8}"
        )
    print("-" * 70)
    print(f"{'best':24} {report.best() or 'none'}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="laix.appkit.bench", description="Run the LAIX decision-class bench.")
    parser.add_argument("--suite", action="append", choices=suite_names(), help="run one or more suites")
    parser.add_argument("--planners", action="store_true", help="compare planners on a chain")
    parser.add_argument("--live", action="store_true", help="compare training-free live planners")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--list", action="store_true", help="list suites and exit")
    parser.add_argument("--fail-under", type=float, default=1.0, help="minimum agreement, default 1.0")
    args = parser.parse_args(argv)

    if args.list:
        for suite in all_suites():
            print(f"{suite.name:24} {suite.description}")
        return 0

    if args.live:
        live_report = run_live_bench()
        if args.json:
            print(json.dumps(live_report.to_dict(), indent=2))
        else:
            print(live_report.summary())
        return 0

    if args.planners:
        planner_report = run_planner_bench()
        if args.json:
            print(json.dumps(planner_report.to_dict(), indent=2))
        else:
            _print_planner_table(planner_report)
        return 0

    report = run_bench(args.suite)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_table(report)
    return 0 if report.agreement >= args.fail_under else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "all_suites",
    "main",
    "run_bench",
    "run_planner_bench",
    "suite_names",
]
