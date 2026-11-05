# Changelog

## Unreleased

### Added

- **Streaming decisions.** `StreamSession`, `TumblingWindow` and the stream fields on
  `Decision` / `DecisionRequest`: event time, dedupe, cooldown, hysteresis, budget,
  backpressure, revisions, deadlines, checkpoints and traces. Queue/sync sources,
  Prometheus counters and a stream bench are included.
- **Engine contract.** `DecisionEngine`, `DecisionProblem`, `Plan` and `EnginePolicy`
  so JEV, an optimizer, a POMDP library or a LAIX planner can sit behind one policy.
- **Execution integrity.** Idempotency keys, `duplicate` receipts, `unknown` outcomes
  and reconciliation in `ExecutionBridge`.
- **Policy authoring and target.** `RulePolicy` with declarative rules, and
  `TargetedPolicy` with `one` / `some` / `all` / `peer` / `gather` targets.
- **TypeScript parity** for the streaming runtime, engine policy, execution integrity
  and target fields.
- **Docs and examples** for streaming, the engine contract, execution integrity and
  the authoring surface.

### Changed

- `ExecutionReceipt` gained `idempotency_key` and the `unknown` / `duplicate` statuses.
- `Decision` and `DecisionRequest` gained `target` and `recipients`.
