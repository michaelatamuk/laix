# Deployment

This page is a production checklist for a host that embeds LAIX. LAIX is a library, not a service:
the host owns the process, network, storage, credentials, model access and execution.

## Topology

```text
agent / automation
        │  signals, options, constraints, approvals
        ▼
LAIX decision runtime  ──►  app kit (optional)
        │                       ├─ execution bridge / saga
        │                       ├─ state, checkpoints, commitments
        │                       ├─ decision records, delivery
        │                       └─ metrics and traces
        ▼
host execution  ──►  external systems
        │
        ▼
receipt / outcome  ──►  record and calibration
```

## Deployment modes

| Mode | Use it when | What the host owns |
|---|---|---|
| Core only | You need one decision and already have execution. | Request data, execution, records. |
| App-kit runtime | You want execution, receipts, records and recovery in one place. | Stores, credentials, transport. |
| Streaming | Decisions arrive from an event stream. | Source, sink, checkpoints, capacity. |

The core is stateless. The app kit adds optional state: experience state, stream checkpoints,
commitment ledgers, outcome stores and decision records. The host still owns the database and the
retention policy.

## Configuration checklist

- **Policies** - choose the policy pack, rules and target mode. See
  [Policies in the app](../01-build/03-policies-in-the-app.md).
- **Constraints** - set hard risk, approval, cost, latency and budget limits.
- **Attention** - set the budget, quiet hours, severity floor and cooldown.
- **Commitments** - load the open ledger and its due times and dependencies.
- **Execution** - register idempotency keys, undo handlers and compensation steps. See
  [Execution and recovery](../03-execute/01-execution-and-recovery.md).
- **Model** - pin the model and planner version; keep it behind an `EnginePolicy`.
- **Time** - use one clock, one timezone policy and ISO-8601 inputs.
- **Retention** - define what records, traces and outcomes are kept and for how long.

## Reliability

- Treat the decision as deterministic for the same request, policy version, clock and planner
  configuration.
- Make every external action idempotent before it reaches the execution adapter.
- Use `ExecutionBridge` receipts; treat `unknown` as unknown, not as success.
- Use `Saga` when one action has several side effects that must be undone together.
- Retry at the host, not inside the decision. Retrying `decide` is safe; retrying an effect is only
  safe with an idempotency key.
- Keep approval and execution separate. A decision with `requires_approval` still needs an explicit
  approval before it becomes an action.
- Put a deadline on model calls and planner runs. LAIX does not enforce wall-clock timeouts for host
  code.

## Observability

- Emit the decision id, trace id, policy version and outcome for every decision.
- Export the stream counters: decided, dropped, suppressed, duplicates, shed and latency.
- Track approval backlog, unknown receipts and failed compensations as separate signals.
- Keep a decision record for every action that changes the world. See
  [Proposals and records](../03-execute/02-proposals-and-records.md).
- Alert on budget violations, repeated unknowns and a rising irreversible-action rate.
- Avoid putting secrets or raw customer text in traces and logs.

## Security and privacy

- Keep secrets and raw data in the host; pass references into LAIX.
- Apply `GroupPolicy` before sharing a decision outside its original target.
- Re-check authorization and approval in the execution adapter.
- Store decision records append-only or in an immutable audit log.
- Read [Security and threat model](../../04-concepts/security.md) and
  [Privacy and trust](../../04-concepts/privacy.md).

## Capacity and latency

- Measure p50, p95 and p99 separately for the decision and the execution.
- Keep the model out of the hot path when deterministic rules are enough.
- Bound input size, option count, model calls and planner depth.
- Load-test the stream buffer and the execution adapter, not just `decide`.
- Use the [bench](01-bench.md) and the
  [evaluation](../../06-research/02-evaluation/benchmark.md) for repeatable numbers.

## Rollout

1. Start in shadow mode with `ShadowPolicy`: compare the new policy with the current one without
   acting on it.
2. Review disagreements, especially irreversible and approval-required cases.
3. Canary a small traffic slice with the new policy version.
4. Keep the previous policy version pinned and be able to route back to it.
5. Record the policy version and model version with every decision.

The policy registry and shadow pattern are in
[Policies in the app](../01-build/03-policies-in-the-app.md#versioning-and-rollout).

## Data retention

The host owns retention. At minimum, decide:

- how long decision records and receipts are kept;
- how long traces and metrics are kept;
- how outcomes and calibration samples are kept;
- how deletion requests are applied to every store;
- which records are needed for audit or EU PLD documentation.

See [EU liability](../../06-research/05-governance/eu-liability.md) for the audit mapping and
[Stores](../04-connect/01-stores.md) for the port contracts.

## Production checklist

- [ ] One clock and one timezone policy.
- [ ] Bounded input, options and model calls.
- [ ] Hard constraints and approval gates in the request.
- [ ] Idempotency keys and undo handlers registered.
- [ ] `unknown` receipts and failed compensations handled.
- [ ] Decision records stored immutably.
- [ ] Secrets and raw data kept out of decisions and logs.
- [ ] Metrics, traces and alerts wired.
- [ ] p95/p99 measured, not assumed.
- [ ] Shadow mode and rollback policy tested.
- [ ] Retention and deletion rules documented.
- [ ] Security and privacy review completed.

## Related

- [Bench](01-bench.md) - the repeatable suites.
- [Metrics](02-metrics.md) - counters and alerts.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the write boundary.
- [Stores](../04-connect/01-stores.md) - persistence and retention.
- [Platform](../04-connect/02-platform.md) - skills and approvals.
- [Delivery](../04-connect/03-delivery.md) - the output channel.
