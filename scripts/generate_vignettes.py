"""Generate the 20 user-study vignettes from live decisions.

The vignettes are study materials, not validation data. Participants choose an action; the file
stores the current LAIX choice so the study can be blinded and scored later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from laix import LiveDecisionEngine, UtilityEngine
from live_bench_common import build_problem

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "validation" / "vignettes-v1.json"
AT = "2026-11-06T10:00:00+00:00"


def opt(
    option_id: str,
    label: str,
    verb: str = "act",
    *,
    benefit: float = 0.6,
    risk: float = 0.0,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "id": option_id,
        "verb": verb,
        "name": label,
        "expected_benefit": benefit,
        "risk": risk,
    }
    payload.update(extra)
    return payload


def vignette(
    vignette_id: str,
    domain: str,
    situation: str,
    options: list[dict[str, Any]],
    *,
    commitments: list[dict[str, Any]] | None = None,
    attention_budget: dict[str, float] | None = None,
    approvals: dict[str, str] | None = None,
) -> dict[str, Any]:
    problem: dict[str, Any] = {
        "subject": domain,
        "at": AT,
        "options": options,
    }
    if commitments:
        problem["commitments"] = commitments
    if attention_budget:
        problem["attention_budget"] = attention_budget
    if approvals:
        problem["approvals"] = approvals
    return {
        "id": vignette_id,
        "domain": domain,
        "situation": situation,
        "options": [
            {"id": item["id"], "label": item["name"], "verb": item["verb"]}
            for item in options
        ],
        "problem": problem,
        "laix_choice": None,
        "laix_verb": None,
        "laix_reason_code": None,
        "laix_rationale": None,
        "baseline_choice": None,
        "baseline_verb": None,
        "baseline_reason_code": None,
        "human_choice": None,
        "notes": "",
    }


VIGNETTES = [
    vignette(
        "v01",
        "customer support",
        "A customer asks for a €780 refund. The policy says amounts above €500 need a human decision.",
        [
            opt("approve", "Approve the refund immediately", benefit=0.8, requires_approval=True),
            opt("ask", "Ask a supervisor to approve", "ask", benefit=0.7),
        ],
    ),
    vignette(
        "v02",
        "on-call operations",
        "A production database is close to its connection limit. A restart is available, but it is disruptive.",
        [
            opt("restart", "Restart the database now", benefit=0.9, risk=0.5, reversible=False),
            opt("scale", "Add capacity and monitor", benefit=0.6),
        ],
    ),
    vignette(
        "v03",
        "data governance",
        "A user asks to delete an account. The request is valid, but deletion cannot be undone.",
        [
            opt("delete", "Delete the account permanently", benefit=0.9, reversible=False),
            opt("archive", "Archive the account and confirm", benefit=0.6),
        ],
    ),
    vignette(
        "v04",
        "healthcare",
        "A patient has not confirmed an appointment tomorrow. The clinic can send a reminder or call.",
        [
            opt("remind", "Send a reminder", "guide", benefit=0.7),
            opt("call", "Call the patient", "ask", benefit=0.8, interrupt_cost=0.5),
            opt("wait", "Wait for the patient", "wait", benefit=0.3),
        ],
    ),
    vignette(
        "v05",
        "sales",
        "A high-value lead opened a proposal three days ago but has not replied.",
        [
            opt("followup", "Send a short follow-up", benefit=0.8),
            opt("wait", "Wait for the lead", "wait", benefit=0.4),
        ],
    ),
    vignette(
        "v06",
        "contracts",
        "A monthly report is due this morning. A fast draft is possible but less accurate.",
        [
            opt(
                "send-fast",
                "Send the fast draft now",
                benefit=0.8,
                commitments={"creates": ["c-report"]},
            ),
            opt(
                "send-careful",
                "Send the careful draft later",
                benefit=0.6,
                commitments={"fulfills": ["c-report"]},
            ),
        ],
        commitments=[{"id": "c-report", "subject": "send the report", "priority": 0.8}],
    ),
    vignette(
        "v07",
        "cloud cost",
        "A budget alert says the monthly spend is 80% used with a week left.",
        [
            opt("throttle", "Throttle non-critical jobs", benefit=0.7),
            opt("observe", "Watch for one more day", "observe", benefit=0.6),
        ],
    ),
    vignette(
        "v08",
        "customer success",
        "A long-running customer sends a complaint that mentions leaving the service.",
        [
            opt("guide", "Offer a retention guide", "guide", benefit=0.7),
            opt("ask", "Ask a human to call", "ask", benefit=0.9, interrupt_cost=0.4),
        ],
    ),
    vignette(
        "v09",
        "security",
        "A critical vulnerability has a patch. The patch may break a legacy integration.",
        [
            opt("patch", "Patch now", benefit=0.9, risk=0.3),
            opt("verify", "Test the patch first", "verify", benefit=0.7),
        ],
    ),
    vignette(
        "v10",
        "inventory",
        "A best-selling item has two days of stock left. The supplier needs a decision today.",
        [
            opt("reorder", "Place the reorder", benefit=0.8, cost=0.4),
            opt("wait", "Wait for a better price", "wait", benefit=0.4),
        ],
    ),
    vignette(
        "v11",
        "scheduling",
        "Three people need a meeting slot. Two slots are possible and one person has not responded.",
        [
            opt("book", "Book the majority slot", benefit=0.7),
            opt("ask", "Ask the missing person", "ask", benefit=0.8, interrupt_cost=0.3),
        ],
    ),
    vignette(
        "v12",
        "content moderation",
        "A post may violate policy but the evidence is ambiguous.",
        [
            opt("remove", "Remove the post now", benefit=0.8, risk=0.4, reversible=False),
            opt("escalate", "Escalate to a human moderator", "escalate", benefit=0.7),
        ],
    ),
    vignette(
        "v13",
        "payments",
        "A card payment failed with a temporary network error.",
        [
            opt("retry", "Retry the payment", benefit=0.8),
            opt("observe", "Observe the next attempt", "observe", benefit=0.5),
        ],
    ),
    vignette(
        "v14",
        "subscriptions",
        "A customer wants to cancel. The contract allows a pause instead.",
        [
            opt("guide", "Offer a pause", "guide", benefit=0.7),
            opt("cancel", "Cancel immediately", benefit=0.8),
        ],
    ),
    vignette(
        "v15",
        "delivery",
        "A delivery is late and the customer is waiting.",
        [
            opt("guide", "Send a new ETA", "guide", benefit=0.7),
            opt("escalate", "Escalate to the carrier", "escalate", benefit=0.8, interrupt_cost=0.3),
        ],
    ),
    vignette(
        "v16",
        "hiring",
        "A candidate is strong but one reference has not replied.",
        [
            opt("ask", "Ask for the missing reference", "ask", benefit=0.8, interrupt_cost=0.3),
            opt("wait", "Wait for the reference", "wait", benefit=0.5),
        ],
    ),
    vignette(
        "v17",
        "laboratory",
        "A lab result is outside the normal range and the patient is not in the clinic.",
        [
            opt("verify", "Verify the sample first", "verify", benefit=0.8),
            opt("escalate", "Escalate to the clinician", "escalate", benefit=0.9, interrupt_cost=0.4),
        ],
    ),
    vignette(
        "v18",
        "platform",
        "An API client is close to its rate limit during a traffic spike.",
        [
            opt("observe", "Observe for five minutes", "observe", benefit=0.6),
            opt("throttle", "Throttle the client now", benefit=0.7),
        ],
    ),
    vignette(
        "v19",
        "warranty",
        "A warranty claim is missing one photo but the customer has a long history.",
        [
            opt("approve", "Approve the claim", benefit=0.8),
            opt("ask", "Ask for the missing photo", "ask", benefit=0.9, interrupt_cost=0.3),
        ],
    ),
    vignette(
        "v20",
        "deployment",
        "A canary release shows a small error increase. The rollback is reversible.",
        [
            opt("rollback", "Roll back the release", benefit=0.8),
            opt("verify", "Investigate for ten minutes", "verify", benefit=0.7),
        ],
    ),
]


def main() -> None:
    engine = LiveDecisionEngine()
    baseline = UtilityEngine()
    for item in VIGNETTES:
        problem = build_problem(item["problem"])
        plan = engine.solve(problem)
        item["laix_choice"] = plan.action_id
        item["laix_verb"] = plan.verb
        item["laix_reason_code"] = plan.reason_code
        item["laix_rationale"] = plan.rationale
        base = baseline.solve(problem)
        item["baseline_choice"] = base.action_id
        item["baseline_verb"] = base.verb
        item["baseline_reason_code"] = base.reason_code

    payload = {
        "schema": "laix/validation-vignettes/v1",
        "version": "1.0.0",
        "note": "User-study materials. human_choice is filled by participants.",
        "vignettes": VIGNETTES,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(VIGNETTES)} vignettes to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
