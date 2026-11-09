# LAIX and the EU Product Liability Directive (2024/2853)

The EU Product Liability Directive (Directive 2024/2853, applicable from
December 2026) makes software and AI systems "products" under the directive.
Deployers can be held liable without proof of fault when an AI system causes
damage. The burden shifts: the claimant may request disclosure of relevant
documentation; refusal creates a presumption of non-compliance.

This note explains how LAIX's decision structure directly answers the audit and
traceability requirements that arise under this framework.

## What the directive requires from an AI decision system

The directive does not prescribe a specific audit format, but practitioners and
legal commentary converge on the following questions a deployer must answer
when a decision is challenged:

1. **What was decided?** Which action was chosen and why?
2. **What was the alternative?** Were safer options available and why were they
   not selected?
3. **What constraints were applied?** Were risk limits, approval rules and
   reversibility requirements in force at the time?
4. **Who was notified?** Was human approval sought when the action crossed a
   threshold?
5. **What was the confidence?** Was the system within its operating envelope?
6. **When was the decision made?** Can the sequence of decisions be reproduced?
7. **Which policy version applied?** Is the decision traceable to a specific
   rule set?

## How each LAIX decision field answers one question

| Directive question | LAIX field | Description |
|---|---|---|
| What was decided? | `verb`, `reason_code`, `rationale` | The chosen verb and the structured reason code explain the decision class (act, verify, escalate, etc.) and why it was taken. |
| What was the alternative? | `breakdown`, `evidence` | The score breakdown lists the considered options with their scores. `evidence` carries the supporting observations. |
| What constraints were applied? | `policy_version`, `breakdown` | The active policy version is recorded in `policy_version`. The score breakdown shows which constraints fired (risk limit, commitment violation, irreversibility flag). |
| Who was notified? | `requires_approval`, `verb = guide / ask / escalate` | The `requires_approval` flag records that a human was required to approve. `guide` and `ask` verbs record that a human was involved. |
| What was the confidence? | `confidence`, `score` | The calibrated confidence and the utility score are fixed at decision time. |
| When was the decision made? | `created_at`, `trace_id`, `decision_id` | Every decision has a unique `decision_id`, a wall-clock `created_at` and a `trace_id` linking it to the request that triggered it. |
| Which policy version applied? | `policy_version` | The policy version is set by the policy at decision time and is immutable in the decision record. |

## Concrete example: a refund decision

```python
from laix import DecisionRequest, Rule, RulePolicy, decide

policy = RulePolicy([
    Rule(
        when={"amount": {"gte": 500}},
        verb="ask",
        reason_code="over_approval_limit",
        requires_approval=True,
    ),
    Rule(when={"amount": {"lt": 500}},  verb="act", reason_code="within_limit"),
])

request = DecisionRequest(
    subject="process refund",
    at="2026-11-06T14:30:00+00:00",
    attributes={"amount": 780, "customer": "VIP-1234"},
)

decision = decide(request, policy=policy)[0]

print(decision.verb)           # ask
print(decision.reason_code)    # over_approval_limit
print(decision.requires_approval)  # True (the rule requires approval)
print(decision.policy_version) # rules.v1
print(decision.decision_id)    # DEC-...
print(decision.created_at)     # 2026-11-06T14:30:00+00:00
```

If this refund is later disputed, the deployer can produce:
- **decision_id**: the exact decision record
- **policy_version**: the rule set in force at the time
- **reason_code = over_approval_limit**: proof that the system required human
  approval before the action ran
- **requires_approval = True**: proof the approval gate was in place

This is a complete audit trail without any log mining or reconstruction.

## Why the decision object is better than a log

Existing approaches record decisions in application logs or database tables
after the fact. These have three problems:

1. **The reason is not structured.** A free-text log cannot be queried by
   reason code or matched to a policy version.
2. **The constraint state is not captured.** Whether a risk limit was active,
   whether an action was flagged as irreversible, whether the approval gate
   fired — none of this is in a standard log entry.
3. **Reconstruction is required.** Proving what the system decided requires
   replaying application state, which may not be possible if state has changed.

LAIX's decision object is the record. It is produced at decision time, carries
all fields in a fixed schema, and is immutable. The deployer stores it; no
reconstruction is needed.

## The seven verbs as a liability signal

The seven LAIX verbs map directly onto the accountability questions the
directive raises:

| Verb | Liability signal |
|---|---|
| `act` | System chose to act; `reversible` and `requires_approval` record whether it was safe to do so. |
| `verify` | System required verification before proceeding; records a checkpoint in the action sequence. |
| `escalate` | System handed control to a human with more authority; records that the boundary was reached. |
| `guide` | System presented the decision to a human; human, not system, made the final choice. |
| `ask` | System requested information or approval; records that the system did not act unilaterally. |
| `observe` | System chose to gather more data before deciding; conservative posture is recorded. |
| `wait` | System chose not to act; records an explicit no-action decision, which is itself a decision. |

The `guide`, `ask` and `escalate` verbs are particularly important: they
record that the system did not act autonomously in a situation that required
human involvement. This is the primary accountability lever under the
directive.

## Practical deployment note

For the directive, the deployer should:

1. Store every `Decision` object (not just the verb) with the `decision_id`
   as the primary key.
2. Store the `policy_version` alongside the policy rule set for the same
   version, so the exact rules in force at decision time can be reproduced.
3. Never overwrite a decision record; use the LAIX revision fields
   (`revision`, `revised_from`) to record corrections.
4. When an action is irreversible (`reversible = False`), record the decision
   before execution, not after. LAIX returns the decision before execution; the
   deployer stores it before running the action.

## Limitations

- LAIX produces the decision record; it does not store it. The deployer owns
  the store.
- The directive applies to damage caused by defects. A correct audit trail does
  not eliminate liability — it provides evidence that due care was taken.
- The legal interpretation of "AI system as product" is still developing;
  consult legal counsel for jurisdiction-specific advice.
- The `policy_version` field records the name the policy assigns to itself.
  The deployer must maintain the mapping from version name to the actual rule
  set text; LAIX does not store policy code.

## References

- Directive 2024/2853 of the European Parliament and of the Council on
  liability for defective products (Product Liability Directive), OJ L,
  18 November 2024.
- European Commission guidance on AI liability, 2023.
- LAIX decision contract: [architecture.md](../04-concepts/01-architecture/01-system-architecture.md)
- LAIX audit fields: `decision_id`, `policy_version`, `trace_id`,
  `created_at`, `deliver`, `record` — see the glossary.
