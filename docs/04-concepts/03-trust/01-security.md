# Security and threat model

LAIX is a decision library. The host owns authentication, authorization, network security,
storage, model access and execution. LAIX must not widen the host's attack surface,
and the host must not trust inputs or model output blindly.

## Trust boundaries

| Boundary | Owner | What crosses it |
|---|---|---|
| Host application | Host | signals, options, constraints, approvals, identity |
| LAIX decision layer | LAIX | decisions, reasons, scores, commitments |
| App kit | Host + LAIX | execution, receipts, records, delivery, state |
| Model or planner | Host | judgments, scores and proposed actions |
| External systems | Host | tickets, incidents, channels, outcomes |

LAIX does not authenticate a signal, verify a model, or grant a permission. Those are host
responsibilities. LAIX makes the resulting decision explicit, constrained and auditable.

## Assets

- decisions and their reasons, scores and confidence;
- commitments and their owners, trust sources, due times, dependencies and status;
- execution receipts and their lifecycle;
- decision records, traces and audit events;
- outcome and calibration data;
- secrets, credentials and raw customer data, which must stay in the host.

## Threats and controls

### 1. Hostile or malformed input

A hostile signal, option or constraint can try to force an unsafe verb or starve the
decision.

Controls:

- validate the request in the host before calling LAIX;
- bound the number of signals, options and attributes;
- keep hard risk, approval and budget constraints in the request;
- do not treat a high `expected_benefit` as authorization;
- log the rejected input, not just the decision.

### 2. Model output as a policy

A model can be wrong, manipulated or prompt-injected. LAIX does not make it trustworthy.

Controls:

- wrap the model in an `PlannerPolicy`; keep the decision contract outside the model;
- validate the model's proposed action against the available options;
- keep hard gates and approval flags above the model;
- prefer deterministic rules for safety, permissions and irreversible actions;
- record the policy version and model version with the decision.

### 3. Over-broad execution

The host owns execution. A decision still needs authorization before it becomes an action.

Controls:

- re-check authorization and approval in the execution adapter;
- make side effects idempotent with an idempotency key;
- use `ExecutionBridge` receipts and `Saga` compensation for multi-step actions;
- treat `unknown` as unknown, not as success;
- keep a human approval step for irreversible or high-value actions.

### 4. Audit tampering

A decision record is only useful if the host stores it safely.

Controls:

- store records append-only or with an immutable audit log;
- use `verify_record` to detect record changes;
- keep the full `trace_id`, `decision_id`, `policy_version` and `created_at`;
- separate the decision store from the execution credentials;
- restrict who can write or delete records.

### 5. Secret and personal-data leakage

Decisions, traces, records, delivery and logs can all carry sensitive fields.

Controls:

- keep secrets and raw customer data in the host;
- pass references in `attributes`, `evidence`, `intent.args` or `rationale`;
- apply `GroupPolicy` before sharing a decision outside its original target;
- keep traces and metrics to ids and reasons where possible;
- apply the host's retention and deletion rules to every store.

### 6. Resource exhaustion

LAIX is deterministic, not a rate limiter.

Controls:

- set input-size, option-count and time limits in the host;
- set a real `HumanAttentionBudget` and execution deadlines;
- rate-limit the adapter that calls a model or planner;
- do not run unbounded planner models in the request path.

### 7. Supply chain

The decision layer is standard-library only. Optional extras and the TypeScript package still need
normal dependency hygiene.

Controls:

- pin and review optional dependencies;
- run `npm audit` and Python dependency checks in the host;
- do not load untrusted policy or model code;
- treat `langgraph` and other comparison adapters as optional, isolated tooling.

### 8. Reported or stale commitments

An external commitment is data from another party. A `reported` promise may be wrong, stale or
malicious, and `source="verified"` is only the host's assertion that it checked the promise.

Controls:

- authenticate and authorize the source that supplies external commitments;
- resolve them just in time and record `source` and `verified_at`;
- use `require_verified=True` for decisions that depend on another owner;
- re-resolve before acting when `verified_at` is old enough to matter;
- never treat a commitment as a signature, an attestation or a settlement;
- keep the resolver, its credentials and any cross-organization protocol in the host or product
  layer.

## Host checklist

- [ ] Authenticate and authorize the caller before `decide`.
- [ ] Validate and bound the request.
- [ ] Keep hard constraints and approval gates in the request.
- [ ] Re-check authorization in the execution adapter.
- [ ] Make side effects idempotent.
- [ ] Store records and receipts immutably.
- [ ] Keep secrets and raw data out of decisions, traces and logs.
- [ ] Set budgets, deadlines and rate limits.
- [ ] Authenticate the source of external commitments and re-check staleness before acting.
- [ ] Apply retention and deletion rules.
- [ ] Report vulnerabilities through [SECURITY.md](../../../SECURITY.md).

## Out of scope

LAIX does not provide:

- authentication or authorization;
- a sandbox for untrusted code;
- transport security;
- a model firewall or prompt-injection filter;
- database encryption or key management;
- a hosted commitment resolver or a shared commitment protocol;
- signatures, attestations, negotiation or settlement;
- network, host or cloud hardening.

Those remain host responsibilities.
