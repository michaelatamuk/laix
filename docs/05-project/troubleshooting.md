# Troubleshooting

Start with the decision, not the symptom. A LAIX decision carries the verb, reason code,
confidence, score breakdown, action and trace identifiers. Inspect those before changing
policy or code.

## First checks

1. Is the request valid? Check `subject`, `at`, options, constraints and timezone.
2. Is the option set what you expect? A verb can only be chosen from the options present.
3. Are hard constraints removing the option you expected? Check risk, approval and cost.
4. Is the attention budget exhausted? Check `AttentionBudget` and the attention breakdown.
5. Is the approval state what you expect? `pending` is not `approved`.
6. Is the policy version the one you think? Check `policy_version`.
7. Is the clock the one you think? `at`, `Context.now` and due times must agree.
8. Is the model or planner returning the action you expect? Wrap it in `EnginePolicy` and
   inspect its output before blaming the contract.

## Symptoms

| Symptom | Likely cause | Check |
|---|---|---|
| It chose `wait` or `observe` | no option fits, budget is spent, or the signal is below the floor | `breakdown`, `alternatives`, constraints, budget |
| It chose `act` when you expected `ask` | approval is not required, or risk is below the gate | `requires_approval`, `risk`, `Constraint` values |
| It asks or escalates too often | attention floor, approval state, or budget is misconfigured | `Context`, `AttentionBudget`, approval map |
| `PolicyError` | malformed request, unknown kind, or invalid option | exception message, input schema |
| `ApprovalRequired` | execution was attempted without approval | approval lifecycle, `requires_approval` |
| `UnknownAction` | action id is not registered with the execution adapter | adapter registry, decision `action_id` |
| Duplicate side effect | retry without an idempotency key | `ExecutionBridge` key, receipt status |
| Missing decision record | recorder or execution bridge was not wired | `Layer(recorder=...)`, `DecisionRecord` store |
| Streaming drops events | buffer full, cooldown or hysteresis | `on_full`, capacity, cooldown, counters |
| Python and TypeScript disagree | version skew or a parity regression | `npm run conformance`, `npm run live-bench` |
| Docs link fails | moved page or renamed file | `python scripts/ci/check_docs_links.py` |
| High latency | model or planner in the hot path | p95/p99, model calls, planner depth |

## Attention reason codes

These are the codes an attention decision can carry.

| Code | Meaning |
|---|---|
| `worth_surfacing` | the signal passed the attention rules |
| `kill_switch` | the kill switch suppressed everything |
| `muted` | the signal kind is muted |
| `snoozed` | the user snoozed this signal |
| `wrong` | the signal was marked wrong |
| `assigned` | the signal belongs to someone else |
| `dismissed` | the user dismissed it |
| `low_confidence` | confidence is below the floor |
| `below_floor` | severity is below the configured floor |
| `already_sent` | the same signal was already delivered |
| `quiet_hours` | quiet hours suppress it |
| `budget` | the interruption budget is exhausted |
| `overdue_escalation` | a critical signal stayed overdue and escalates |
| `act` | the attention rules choose to act |
| `ask_approval` | the attention rules choose to ask for approval |

## Common planner and policy codes

| Code | Meaning |
|---|---|
| `expected_utility` | utility chose the best expected value |
| `commitment_aware` | the commitment planner adjusted the choice |
| `execution_aware` | the execution planner adjusted the choice |
| `attention_aware` | the attention planner adjusted the choice |
| `live_decision` | the integrated live planner chose the action |
| `mdp_plan` / `pomdp_plan` | a model-based planner returned a plan |
| `policy_rule` | an authored rule fired |
| `no_rule` | no authored rule matched |
| `safety_blocked` / `no_safe_option` | a safety constraint removed the action |
| `ask_preference` | the preference policy needs a choice |
| `verify_outcome` | the verification policy wants a check |
| `escalate_to_target` | the escalation policy handed over |
| `replan` | the replanning policy found no feasible plan |

Reason codes are part of the policy contract. Treat a change to a code as a behaviour change
and record it in `CHANGELOG.md`.

## Execution issues

- **Approval**: a decision with `requires_approval` is not a permission. Move the proposal
  through approve or reject, then execute.
- **Unknown outcome**: a receipt with status `unknown` must be reconciled before retrying.
- **Compensation**: use `Saga` when a later step fails; each earlier step needs a registered
  undo or compensation.
- **Idempotency**: the same key must return the same receipt, not run the side effect twice.

## Performance

- Measure the decision and the execution separately.
- Remove model calls from the hot path when deterministic rules are enough.
- Reduce option count, planner depth or stream capacity before adding infrastructure.
- Use the [benchmark](../03-appkit/08-laix-bench.md) and
  [evaluation](../06-research/02-evaluation/benchmark.md) for repeatable numbers.

## Getting help

Include the version, package, a minimal request, the actual decision, the expected decision
and the reason code. See [SUPPORT.md](../../SUPPORT.md).
