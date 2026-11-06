"""Generate the deterministic LAIX live-bench v1 corpus.

The case files are committed; this script keeps the corpus reproducible and
makes the category/split balance explicit. Run from the repository root:

    python scripts/novelty/bench/generate_live_cases.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "benchmarks" / "cases"
AT = "2026-11-01T10:00:00+00:00"
PAST = "2026-11-01T09:00:00+00:00"
FUTURE = "2026-11-01T12:00:00+00:00"


def option(
    option_id: str,
    verb: str = "act",
    *,
    benefit: float = 0.6,
    risk: float = 0.0,
    cost: float = 0.0,
    interrupt: float = 0.0,
    latency: float = 0.0,
    reversible: bool = True,
    approval: bool = False,
    fulfills: tuple[str, ...] = (),
    violates: tuple[str, ...] = (),
    creates: tuple[str, ...] = (),
    unknown_risk: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": option_id,
        "verb": verb,
        "name": option_id.replace("-", " "),
        "expected_benefit": round(benefit, 3),
        "risk": round(risk, 3),
        "cost": round(cost, 3),
        "interrupt_cost": round(interrupt, 3),
        "latency_ms": latency,
        "reversible": reversible,
        "requires_approval": approval,
    }
    commitments = {}
    if fulfills:
        commitments["fulfills"] = list(fulfills)
    if violates:
        commitments["violates"] = list(violates)
    if creates:
        commitments["creates"] = list(creates)
    if commitments:
        payload["commitments"] = commitments
    if unknown_risk is not None:
        payload["unknown_risk"] = round(unknown_risk, 3)
    return payload


def case(
    case_id: str,
    name: str,
    tags: tuple[str, ...],
    expected: tuple[str, ...],
    options: list[dict[str, Any]],
    *,
    situation: dict[str, Any] | None = None,
    commitments: list[dict[str, Any]] | None = None,
    attention_budget: dict[str, float] | None = None,
    approvals: dict[str, str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    problem: dict[str, Any] = {"subject": name, "at": AT, "options": options}
    if situation is not None:
        problem["situation"] = situation
    if commitments is not None:
        problem["commitments"] = commitments
    if attention_budget is not None:
        problem["attention_budget"] = attention_budget
    if approvals is not None:
        problem["approvals"] = approvals
    return {
        "id": case_id,
        "name": name,
        "tags": list(tags),
        "expected_actions": list(expected),
        "note": note,
        "problem": problem,
    }


def constraint(kind: str, value: float, identifier: str | None = None) -> dict[str, Any]:
    return {
        "id": identifier or f"{kind}-limit",
        "kind": kind,
        "value": value,
        "hard": True,
    }


def situation(*constraints: dict[str, Any], subject: str = "case") -> dict[str, Any]:
    return {"id": "situation", "subject": subject, "constraints": list(constraints)}


def commitment(
    commitment_id: str,
    *,
    subject: str = "promise",
    due: str | None = None,
    priority: float = 0.5,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": commitment_id,
        "subject": subject,
        "priority": priority,
    }
    if due is not None:
        payload["due"] = due
    return payload


def plain_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        best = 0.8 + 0.01 * (index % 4)
        weak = 0.35 + 0.02 * (index % 4)
        cases.append(
            case(
                f"{prefix}_plain_{index:02d}",
                "plain utility choice",
                ("plain",),
                ("best",),
                [
                    option("best", benefit=best),
                    option("weak", benefit=weak),
                ],
                note="The option with the highest benefit is correct; no other concern applies.",
            )
        )
    return cases


def promise_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        cid = f"c{index}"
        due = PAST if index % 3 == 0 else (FUTURE if index % 3 == 1 else None)
        priority = 0.4 + 0.1 * (index % 5)
        cases.append(
            case(
                f"{prefix}_promise_{index:02d}",
                "keep the open promise",
                ("promise",),
                ("keep",),
                [
                    option("keep", benefit=0.6, fulfills=(cid,)),
                    option("break", benefit=0.9, violates=(cid,)),
                ],
                commitments=[commitment(cid, due=due, priority=priority)],
                note="Keeping the open commitment is correct even at a lower immediate benefit.",
            )
        )
    return cases


def execution_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        kind = index % 4
        if kind == 0:
            risky = option("risky", benefit=0.9, reversible=False)
            note = "The irreversible option is not worth the small benefit gain."
        elif kind == 1:
            risky = option("risky", benefit=0.9, unknown_risk=0.9)
            note = "A high unknown-outcome risk makes the safe option correct."
        elif kind == 2:
            risky = option("risky", benefit=0.9, approval=True)
            note = "An approval step costs execution and attention; the safe option wins."
        else:
            risky = option("risky", benefit=0.9, reversible=False, unknown_risk=0.5)
            note = "Irreversibility plus unknown risk makes the safe option correct."
        cases.append(
            case(
                f"{prefix}_execution_{index:02d}",
                "avoid execution risk",
                ("execution",),
                ("safe",),
                [option("safe", benefit=0.6), risky],
                note=note,
            )
        )
    return cases


def attention_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        kind = index % 5
        if kind == 0:
            cases.append(
                case(
                    f"{prefix}_attention_{index:02d}",
                    "spend available attention",
                    ("attention",),
                    ("ask",),
                    [
                        option("ask", "ask", benefit=0.9, interrupt=0.2),
                        option("act", benefit=0.6),
                    ],
                    attention_budget={"total": 1.0, "spent": 0.0},
                    note="The human-facing option fits the remaining attention budget.",
                )
            )
        elif kind == 1:
            cases.append(
                case(
                    f"{prefix}_attention_{index:02d}",
                    "budget exhausted",
                    ("attention",),
                    ("act",),
                    [
                        option("ask", "ask", benefit=0.9, interrupt=0.2),
                        option("act", benefit=0.6),
                    ],
                    attention_budget={"total": 1.0, "spent": 1.0},
                    note="The budget is exhausted, so the direct action is correct.",
                )
            )
        elif kind == 2:
            cases.append(
                case(
                    f"{prefix}_attention_{index:02d}",
                    "approval rejected",
                    ("attention",),
                    ("fallback",),
                    [
                        option("ask", "ask", benefit=0.9, interrupt=0.1),
                        option("fallback", benefit=0.5),
                    ],
                    approvals={"ask": "rejected"},
                    note="A rejected approval must not be chosen.",
                )
            )
        elif kind == 3:
            cases.append(
                case(
                    f"{prefix}_attention_{index:02d}",
                    "escalation is too expensive",
                    ("attention",),
                    ("act",),
                    [
                        option("escalate", "escalate", benefit=0.9, interrupt=0.5),
                        option("act", benefit=0.6),
                    ],
                    attention_budget={"total": 1.0, "spent": 0.7},
                    note="Escalation costs more attention than remains.",
                )
            )
        else:
            cases.append(
                case(
                    f"{prefix}_attention_{index:02d}",
                    "guide within budget",
                    ("attention",),
                    ("guide",),
                    [
                        option("guide", "guide", benefit=0.85, interrupt=0.1),
                        option("act", benefit=0.55),
                    ],
                    attention_budget={"total": 1.0, "spent": 0.0},
                    note="The guide option is the best use of available attention.",
                )
            )
    return cases


def timing_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        if index % 2 == 0:
            cid = f"t{index}"
            due = PAST if index % 4 == 0 else FUTURE
            cases.append(
                case(
                    f"{prefix}_timing_{index:02d}",
                    "time-sensitive promise",
                    ("timing", "promise"),
                    ("keep",),
                    [
                        option("keep", benefit=0.6, fulfills=(cid,)),
                        option("break", benefit=0.9, violates=(cid,)),
                    ],
                    commitments=[commitment(cid, due=due, priority=0.7)],
                    note="The promise is due or approaching; keeping it is correct.",
                )
            )
        else:
            cases.append(
                case(
                    f"{prefix}_timing_{index:02d}",
                    "latency limit",
                    ("timing",),
                    ("fast",),
                    [
                        option("fast", benefit=0.6, latency=50),
                        option("slow", benefit=0.9, latency=500),
                    ],
                    situation=situation(constraint("latency", 100), subject="latency limit"),
                    note="The hard latency limit excludes the slower, higher-benefit option.",
                )
            )
    return cases


def conflict_cases(count: int, prefix: str) -> list[dict[str, Any]]:
    cases = []
    for index in range(count):
        kind = index % 4
        cid = f"cc{index}"
        if kind == 0:
            options = [
                option("fast", benefit=1.0, reversible=False, violates=(cid,)),
                option("safe", benefit=0.6, fulfills=(cid,)),
            ]
            tags = ("conflict", "promise", "execution")
            note = "Fast breaks a promise and is irreversible; safe keeps the promise."
        elif kind == 1:
            options = [
                option("fast", "ask", benefit=1.0, interrupt=0.4, violates=(cid,)),
                option("safe", benefit=0.6, fulfills=(cid,)),
            ]
            tags = ("conflict", "promise", "attention")
            note = "Fast breaks a promise and costs attention; safe keeps it directly."
        elif kind == 2:
            options = [
                option("fast", "ask", benefit=1.0, interrupt=0.4, reversible=False),
                option("safe", benefit=0.6),
            ]
            tags = ("conflict", "execution", "attention")
            note = "Fast is irreversible and needs attention; safe is direct and reversible."
        else:
            options = [
                option(
                    "fast",
                    "ask",
                    benefit=1.0,
                    reversible=False,
                    interrupt=0.5,
                    violates=(cid,),
                ),
                option("safe", benefit=0.6, fulfills=(cid,)),
            ]
            tags = ("conflict", "promise", "execution", "attention")
            note = "All three concerns fire; safe is the only option that satisfies them."
        cases.append(
            case(
                f"{prefix}_conflict_{index:02d}",
                "conflicting concerns",
                tags,
                ("safe",),
                options,
                commitments=(
                    [commitment(cid, due=PAST, priority=0.7)] if kind != 2 else None
                ),
                attention_budget={"total": 0.5, "spent": 0.1},
                note=note,
            )
        )
    return cases


def build_split(split: str, counts: dict[str, int]) -> dict[str, Any]:
    cases = []
    for category, count in counts.items():
        generator = {
            "plain": plain_cases,
            "promise": promise_cases,
            "execution": execution_cases,
            "attention": attention_cases,
            "timing": timing_cases,
            "conflict": conflict_cases,
        }[category]
        cases.extend(generator(count, split))
    return {
        "schema": "laix/live-bench/v1",
        "version": "1.0.0",
        "split": split,
        "note": f"LAIX live-bench v1 {split} split.",
        "cases": cases,
    }


SPLITS = {
    "dev": {
        "promise": 12,
        "execution": 12,
        "attention": 12,
        "timing": 9,
        "conflict": 15,
        "plain": 12,
    },
    "test": {
        "promise": 5,
        "execution": 5,
        "attention": 5,
        "timing": 4,
        "conflict": 6,
        "plain": 5,
    },
    "adversarial": {
        "promise": 3,
        "execution": 3,
        "attention": 3,
        "timing": 2,
        "conflict": 4,
        "plain": 3,
    },
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for split, counts in SPLITS.items():
        payload = build_split(split, counts)
        target = OUT / f"{split}-cases-v1.json"
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"{target.relative_to(ROOT)}: {len(payload['cases'])} cases")


if __name__ == "__main__":
    main()
