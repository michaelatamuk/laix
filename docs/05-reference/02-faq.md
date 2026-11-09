# FAQ

## What is LAIX?

A live decision layer for AI agents that act in the real world. It turns a request
into one decision with a reason, confidence and trail.

## Is LAIX an agent framework?

No. An agent framework owns orchestration, memory, tools and the model loop. LAIX owns the decision
inside one task. It can sit inside LangGraph, Temporal, CrewAI, an in-house runtime or a plain
service. See [Decision models](../04-concepts/02-positioning/01-decision-models.md).

## Does LAIX use a model?

The built-in policies are deterministic rules and the default path is training-free. A planner can use a
world model the host supplies: states, transitions and rewards. A pretrained model can sit behind
`PlannerPolicy` or inside a custom policy, and the decision contract stays the same.

## Does LAIX train a model?

No. Outcome learning, calibration and causal inference use the outcomes the host measures. The
learners update from data; they do not train a foundation model.

## Where does execution happen?

In the host. The optional app kit provides an execution bridge, receipts, recovery, proposals and
records. LAIX does not open a database, call a provider or deliver a message on its own.

## What does a decision carry?

A verb, reason code, confidence, rationale, optional action and intent, approval, evidence, target,
decision id and trace id. The full shape is in
[the decision contract](../02-decision/01-contract/01-decision-contract.md).

## What is the novelty?

The integration: one training-free decision contract for commitments, execution risk, human
attention, calibration and decision time. `LiveCompositePlanner` combines the four live concerns in one
plan. The contract also carries approval, reversibility, verification and the audit trail, which are
usually rebuilt in each app.

## When should I use it?

When several agents, tasks or products need consistent, timely, safe and auditable decisions, and you
want one contract instead of separate decision logic in each.

For one app with one decision, app code with a model is simpler. LAIX pays off when the decision
layer would otherwise be written again in several places.

## Is it production-ready?

LAIX is a library with host-controlled execution and storage. Production use needs the host checklist:
authentication, authorization, bounded inputs, idempotency, immutable records, budgets, retention and
security review. See [Security](../04-concepts/03-trust/01-security.md) and
[Deployment](../03-appkit/05-operate/03-deployment.md).

The repository does not claim a `1.0` or production validation. External validation is still pending.

## What evidence exists?

- internal regression: LAIX-Bench, 25 cases across 10 suites;
- live decision benchmark: 30-case frozen test split, with a non-significant glue baseline;
- continuity benchmark: 12 episodes and 60 decisions, synthetic mechanism test;
- external: Sev1-Bench null result and a small tau-bench guardrail signal;
- parity and invariants in CI.

The claim-evidence map states the scope of each result:
[evidence map](../07-research/02-evaluation/evidence-map.md). The research plan is in
[Research and evidence](../07-research/README.md).

## Does LAIX store data?

No. LAIX defines the store contracts; the host owns the database, retention and deletion. See
[Stores](../03-appkit/04-connect/01-stores.md) and [Privacy](../04-concepts/03-trust/02-privacy.md).

## Which languages are supported?

Python and TypeScript. The two packages share the decision contract, the reason codes and the test
vectors.

## How do I start?

1. [Quickstart](../01-start/02-first-steps/01-quickstart.md) for the first decision.
2. [Decision overview](../02-decision/README.md) for the contract and the mechanisms.
3. [App-kit overview](../03-appkit/README.md) for execution, records and stores.
4. [Decision models](../04-concepts/02-positioning/01-decision-models.md) if you already use JEV or another model.

## What are the limits?

- The internal corpus is designed and maintained by the project.
- The continuity result is synthetic.
- The external results are a null result and a small single-trial signal.
- The integration advantage over a hand-built glue baseline is not significant on 30 cases.
- Cross-system fairness needs a runnable adapter and an independent replication.

The evidence map is the source of truth for those limits.

## Where is the vocabulary?

See the [glossary](01-glossary.md).
