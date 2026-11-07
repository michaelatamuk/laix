"""Decision-continuity episode benchmark v0.

Each episode is a short sequence of decisions. The same options are shown to a stateless
utility planner and to LiveDecisionEngine. Only the stateful planner sees the open commitment,
the attention budget, the approval state and the receipt state.

The reference policy is hand-written and deterministic. It is the ground truth for the episode.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from laix import (
    ActionOption,
    AttentionBudget,
    Commitment,
    DecisionProblem,
    LiveDecisionEngine,
    UtilityEngine,
)

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "results" / "continuity-benchmark" / "metrics" / "summary.json"
CORPUS = ROOT / "benchmarks" / "continuity" / "v1" / "episodes.json"


@dataclass
class Episode:
    id: str
    due_step: int
    receipt_outcome: str
    budget_total: float
    steps: int = 5


@dataclass
class State:
    step: int = 0
    c1_open: bool = True
    c1_fulfilled: bool = False
    budget_spent: float = 0.0
    approval: str = "pending"
    receipt: str = "none"
    approval_violations: int = 0
    budget_violations: int = 0
    duplicate_acts: int = 0
    escalated: bool = False
    actions: list[str] = field(default_factory=list)


def episodes() -> list[Episode]:
    rows = json.loads(CORPUS.read_text(encoding="utf-8"))
    return [Episode(**row) for row in rows]


def base_options() -> tuple[ActionOption, ...]:
    """Options with no episode state. Used by the stateless planner every step."""
    return (
        ActionOption(
            id="act",
            verb="act",
            name="act now",
            expected_benefit=0.9,
            risk=0.0,
            reversible=True,
            requires_approval=True,
            interrupt_cost=0.6,
            params={
                "commitments": {"fulfills": ["c1"]},
                "execution": {"unknown_risk": 0.0},
                "attention": {"interrupt_cost": 0.6},
            },
        ),
        ActionOption(
            id="ask",
            verb="ask",
            name="ask for approval",
            expected_benefit=0.75,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.25,
        ),
        ActionOption(
            id="verify",
            verb="verify",
            name="verify the receipt",
            expected_benefit=0.6,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.1,
            params={"execution": {"unknown_risk": 0.0}},
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait",
            expected_benefit=0.2,
            risk=0.0,
            reversible=True,
        ),
        ActionOption(
            id="escalate",
            verb="escalate",
            name="escalate",
            expected_benefit=0.25,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.3,
        ),
    )


def options(state: State) -> tuple[ActionOption, ...]:
    act_benefit = 0.9 if state.c1_open else 0.35
    if state.receipt == "unknown":
        act_benefit = 0.35
    elif state.receipt == "failed":
        act_benefit = 0.2
    verify_benefit = 0.9 if state.receipt == "unknown" else 0.2
    escalate_benefit = 0.9 if state.receipt == "failed" else 0.25
    wait_benefit = 0.6 if state.c1_fulfilled and state.receipt in {"ok", "none"} else 0.2
    return (
        ActionOption(
            id="act",
            verb="act",
            name="act now",
            expected_benefit=act_benefit,
            risk=0.0,
            reversible=True,
            requires_approval=True,
            interrupt_cost=0.6,
            params={
                "commitments": {"fulfills": ["c1"]},
                "execution": {"unknown_risk": 0.0},
                "attention": {"interrupt_cost": 0.6},
            },
        ),
        ActionOption(
            id="ask",
            verb="ask",
            name="ask for approval",
            expected_benefit=0.75,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.25,
        ),
        ActionOption(
            id="verify",
            verb="verify",
            name="verify the receipt",
            expected_benefit=verify_benefit,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.1,
            params={"execution": {"unknown_risk": 0.0}},
        ),
        ActionOption(
            id="wait",
            verb="wait",
            name="wait",
            expected_benefit=wait_benefit,
            risk=0.0,
            reversible=True,
        ),
        ActionOption(
            id="escalate",
            verb="escalate",
            name="escalate",
            expected_benefit=escalate_benefit,
            risk=0.0,
            reversible=True,
            interrupt_cost=0.3,
        ),
    )


def reference_action(state: State) -> str:
    if state.c1_open and state.approval != "approved":
        return "ask"
    if state.receipt == "unknown":
        return "verify"
    if state.receipt == "failed":
        return "escalate"
    if state.c1_open and state.step >= 1:
        return "act"
    if state.budget_spent >= 0.75:
        return "wait"
    return "wait"


def apply_action(state: State, action_id: str, episode: Episode) -> None:
    state.actions.append(action_id)
    if action_id == "ask":
        state.approval = "approved"
        state.budget_spent += 0.25
    elif action_id == "act":
        if state.approval != "approved":
            state.approval_violations += 1
        if not state.c1_open:
            state.duplicate_acts += 1
        else:
            state.c1_open = False
            state.c1_fulfilled = True
        state.budget_spent += 0.35
        state.receipt = "unknown"
    elif action_id == "verify":
        state.budget_spent += 0.1
        if state.receipt == "unknown":
            state.receipt = episode.receipt_outcome
    elif action_id == "escalate":
        state.budget_spent += 0.2
        state.escalated = True
    if state.budget_spent > episode.budget_total:
        state.budget_violations += 1


def problem_for(episode: Episode, state: State) -> DecisionProblem:
    due_minute = (state.step + 1) * 60
    due = f"2026-11-01T10:{due_minute:02d}:00+00:00"
    attributes: dict[str, object] = {
        "commitments": (
            Commitment(id="c1", subject=episode.id, due=due, priority=0.9),
        )
        if state.c1_open
        else (),
        "attention_budget": AttentionBudget(total=episode.budget_total, spent=state.budget_spent),
        "approvals": {"act": state.approval},
    }
    if state.receipt in {"unknown", "failed"}:
        attributes["execution_state"] = {"act": state.receipt}
    return DecisionProblem(
        subject=episode.id,
        at=f"2026-11-01T10:{state.step * 60:02d}:00+00:00",
        options=options(state),
        attributes=attributes,
    )


def effective_action(plan: object, state: State) -> str:
    if getattr(plan, "requires_approval", False) and state.approval != "approved":
        return "ask"
    return str(plan.action_id)


def run_episode(episode: Episode) -> dict[str, object]:
    reference = State()
    stateless = State()
    stateful = State()

    for step in range(episode.steps):
        for state in (reference, stateless, stateful):
            state.step = step

        ref = reference_action(reference)
        apply_action(reference, ref, episode)

        # The stateless planner gets the same static options every step and no episode state.
        bare = DecisionProblem(subject=episode.id, at="2026-11-01T10:00:00+00:00", options=base_options())
        stateless_plan = UtilityEngine().solve(bare)
        apply_action(stateless, effective_action(stateless_plan, stateless), episode)

        stateful_plan = LiveDecisionEngine().solve(problem_for(episode, stateful))
        apply_action(stateful, effective_action(stateful_plan, stateful), episode)

    def metrics(state: State) -> dict[str, object]:
        return {
            "actions": state.actions,
            "promise_kept": state.c1_fulfilled and not state.c1_open,
            "budget_adhered": state.budget_violations == 0,
            "approval_correct": state.approval_violations == 0,
            "continuity_errors": state.duplicate_acts,
            "budget_spent": round(state.budget_spent, 3),
            "success": (
                state.c1_fulfilled
                and not state.c1_open
                and state.budget_violations == 0
                and state.approval_violations == 0
                and state.duplicate_acts == 0
            ),
        }

    return {
        "episode": episode.id,
        "due_step": episode.due_step,
        "receipt_outcome": episode.receipt_outcome,
        "budget_total": episode.budget_total,
        "reference": metrics(reference),
        "stateless": metrics(stateless),
        "stateful": metrics(stateful),
    }


def summarise(rows: list[dict[str, object]]) -> dict[str, object]:
    def rate(key: str) -> dict[str, float]:
        return {
            "success": round(sum(1 for row in rows if row[key]["success"]) / len(rows), 4),
            "promise_kept": round(sum(1 for row in rows if row[key]["promise_kept"]) / len(rows), 4),
            "budget_adhered": round(sum(1 for row in rows if row[key]["budget_adhered"]) / len(rows), 4),
            "approval_correct": round(sum(1 for row in rows if row[key]["approval_correct"]) / len(rows), 4),
            "continuity_errors": sum(int(row[key]["continuity_errors"]) for row in rows),
        }

    return {
        "episodes": len(rows),
        "steps": sum(len(row["reference"]["actions"]) for row in rows),
        "reference": rate("reference"),
        "stateless": rate("stateless"),
        "stateful": rate("stateful"),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=RESULTS)
    args = parser.parse_args()

    rows = [run_episode(episode) for episode in episodes()]
    summary = summarise(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"episodes: {summary['episodes']}  decisions: {summary['steps']}")
    print(f"{'policy':<12} {'success':>8} {'promise':>8} {'budget':>7} {'approval':>9} {'errors':>7}")
    for name in ("reference", "stateless", "stateful"):
        item = summary[name]
        print(
            f"{name:<12} {item['success']:>8.2%} {item['promise_kept']:>8.2%} "
            f"{item['budget_adhered']:>7.2%} {item['approval_correct']:>9.2%} "
            f"{item['continuity_errors']:>7}"
        )
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
