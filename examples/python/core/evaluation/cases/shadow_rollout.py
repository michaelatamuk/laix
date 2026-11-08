"""Shadow policy rollout: test -> compare -> promote.

A safe pattern for introducing a new policy in production:

  Phase 1  Run the candidate behind a ShadowPolicy.
           Every live request goes through both primary and candidate.
           The candidate's answer is recorded but not used.

  Phase 2  Inspect the disagreements.
           If the candidate disagrees on fewer than a threshold of requests,
           promote it.

  Phase 3  Promote by swapping primary ↔ candidate.
           The old primary is kept as the new shadow.

This example uses a fixed list of requests as a stand-in for a live request
stream. In production, replace the loop with your existing request path.
"""

from __future__ import annotations

from dataclasses import dataclass

from laix import DecisionRequest, Rule, RulePolicy, ShadowPolicy

# ------------------------------------------------------------------
# Two policies to compare
# ------------------------------------------------------------------

# Production policy: escalate all requests above €500
primary_policy = RulePolicy(
    [Rule(when={"amount": {"gte": 500}}, verb="escalate", reason_code="over_limit")]
)

# Candidate policy: only escalate above €1000; approve smaller requests
candidate_policy = RulePolicy(
    [
        Rule(when={"amount": {"gte": 1000}}, verb="escalate", reason_code="over_limit"),
        Rule(when={"amount": {"lt": 1000}}, verb="act", reason_code="within_limit"),
    ]
)

shadow = ShadowPolicy(primary_policy, candidate_policy)

# ------------------------------------------------------------------
# Phase 1: shadow run
# ------------------------------------------------------------------

REQUESTS = [
    DecisionRequest(
        subject="refund",
        at="2026-11-01T10:00:00+00:00",
        attributes={"amount": amount},
    )
    for amount in [200, 480, 520, 750, 1050, 1200]
]

PROMOTION_THRESHOLD = 0.5   # promote if candidate disagrees on <=50 % of requests

print("Phase 1 - shadow run (primary decision is live; candidate is recorded)")
print()
print(f"{'amount':>8}  {'primary':>10}  {'candidate':>10}  agrees")
print("-" * 50)

for req in REQUESTS:
    decisions = shadow.decide(req)
    primary_verb = decisions[0].verb
    # find the candidate's answer from the differences recorded so far
    # We re-decide to show both sides
    primary_plan = primary_policy.decide(req)
    candidate_plan = candidate_policy.decide(req)
    p_verb = primary_plan[0].verb if primary_plan else "-"
    c_verb = candidate_plan[0].verb if candidate_plan else "-"
    agrees = "yes" if p_verb == c_verb else "no"
    amount = req.attributes.get("amount", "?")
    print(f"{amount:>8}  {p_verb:>10}  {c_verb:>10}  {agrees}")

# ------------------------------------------------------------------
# Phase 2: inspect disagreement rate
# ------------------------------------------------------------------

total = len(REQUESTS)
disagreements = len(shadow.differences)
rate = disagreements / total if total else 0.0

print()
print(f"Phase 2 - disagreement rate: {disagreements}/{total} = {rate:.0%}")

if rate <= PROMOTION_THRESHOLD:
    print(f"  Rate <= {PROMOTION_THRESHOLD:.0%}: candidate qualifies for promotion.")
else:
    print(f"  Rate > {PROMOTION_THRESHOLD:.0%}: candidate needs more review.")

# ------------------------------------------------------------------
# Phase 3: promote
# ------------------------------------------------------------------

print()
print("Phase 3 - promote candidate to primary; keep old primary as new shadow")
print()

new_shadow = ShadowPolicy(candidate_policy, primary_policy)

test_req = DecisionRequest(
    subject="refund",
    at="2026-11-01T10:00:00+00:00",
    attributes={"amount": 750},
)
promoted_decision = new_shadow.decide(test_req)[0]
print(f"  request amount=750: primary (promoted) -> {promoted_decision.verb}")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

print()
print("Rollout pattern:")
print("  1. Wrap with ShadowPolicy(primary, candidate)")
print("  2. Run against live traffic; candidate never affects the response")
print("  3. Check shadow.differences - disagreement rate below threshold -> promote")
print("  4. Swap: ShadowPolicy(candidate, primary)")
print("  5. Repeat until the new policy is fully trusted")
