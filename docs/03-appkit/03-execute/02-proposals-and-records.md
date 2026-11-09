# Proposals and records

Two audit objects sit around execution:

- a **proposal** is the app-facing form of an action that needs a person;
- a **decision record** is the audit trail of what was decided, approved, executed and undone.

Both are storage-free. The app owns the store; the app kit owns the lifecycle.

## Proposal

A proposal moves through four states:

```text
pending -> approved -> applied -> undone
pending -> rejected
```

| Field | Meaning |
|---|---|
| `id` | Proposal id. |
| `title` | Short title for the person. |
| `summary` | What is proposed and what it changes. |
| `decision_id` | The decision that produced the proposal. |
| `action_id` | The action the proposal would apply. |
| `status` | `pending`, `approved`, `rejected`, `applied` or `undone`. |
| `created_at` / `created_by` | Who created it and when. |
| `approved_by` / `approved_at` | Who approved or rejected it. |
| `applied_at` | When the host applied it. |
| `undo_hint` | How to reverse it. |
| `payload` | App-owned data. |

```python
from laix import Proposal, apply_proposal, approve_proposal, undo_proposal

proposal = Proposal(
    id="p-1",
    title="Change the delivery window",
    summary="Move Friday's delivery to Saturday morning.",
    decision_id="d-1",
)

approved = approve_proposal(proposal, by="owner")
applied = apply_proposal(approved)
undone = undo_proposal(applied)

print(proposal.status, approved.status, applied.status, undone.status)
```

`approve_proposal`, `reject_proposal`, `apply_proposal` and `undo_proposal` enforce the state
machine. `PROPOSAL_STATUSES` lists the valid states. An invalid transition raises `ValueError`.

## Decision record

A decision record moves through:

```text
draft -> approved -> executed -> undone
draft -> rejected
```

| Field | Meaning |
|---|---|
| `id` | Record id. |
| `title` / `summary` | What was decided, in human terms. |
| `decision` | The decision text, confidence and rationale. |
| `evidence` | `EvidenceRef` items that support the decision. |
| `approval` | `Approval`: required, state, approver, time and note. |
| `status` | `draft`, `approved`, `rejected`, `executed` or `undone`. |
| `created_at` / `updated_at` | Lifecycle timestamps. |
| `audit` | Append-only `AuditEvent` items. |
| `undo` | `Undo`: available, how and when. |
| `metadata` | App-owned data. |
| `hash` | Fingerprint of the record content. |

```python
from laix import EvidenceRef, approve_record, create_record, mark_executed, verify_record

record = create_record(
    title="Pay the electricity bill",
    decision="Pay 42.00 today.",
    evidence=(EvidenceRef(id="bill-1", quote="The bill is due today."),),
)

approved = approve_record(record, by="owner")
executed = mark_executed(approved, by="owner")

print(executed.status, verify_record(executed))
```

`create_record`, `approve_record`, `reject_record`, `mark_executed` and `verify_record` are the
package-level surface. The record carries an `Undo` field; the `undo` helper lives in
`laix.appkit.audit.decision_record` for hosts that need to reverse a record. `verify_record` checks
the fingerprint after each read.

## Audit parts

| Contract | Contents |
|---|---|
| `Approval` | `required`, `state`, `by`, `at`, `note`. |
| `AuditEvent` | `at`, `actor`, `event`, `detail`. |
| `Undo` | `available`, `how`, `at`. |
| `EvidenceRef` | `id`, `quote`, optional source fields. |

Keep the audit trail append-only. Do not edit an event or a record in place; create the next record
state and keep the fingerprint.

## Where the store lives

The proposal and the record are values. The host decides where they are saved, how long they are
kept and how deletion requests are applied. The [stores page](../04-connect/01-stores.md) covers the
ports; [Deployment](../05-operate/03-deployment.md) covers retention.

## TypeScript

TypeScript uses `createDecisionRecord`, `approveRecord`, `rejectRecord`, `markExecuted`, `undoRecord`
and `verifyRecord` for the record lifecycle. It uses `createProposal`, `approveProposal`,
`rejectProposal`, `applyProposal` and `undoProposal` for the proposal lifecycle. The state types are
`ProposalStatus`, `RecordStatus`, `DECISION_STATUSES`, `CreateDecisionInput` and `UndoInput`.
`canonical` produces canonical JSON for fingerprints, and `evidenceFromQuotes` builds
`EvidenceRef` values.

## Boundary

- A proposal is not an execution. It becomes one only after approval and `apply`.
- A decision record is not a receipt. The record is the audit lifecycle; the receipt is what the
  execution boundary returned.
- A record can exist without an action, for example when a decision is rejected.
- Approval and undo are explicit state transitions, not side effects.

## Related

- [Execution and recovery](01-execution-and-recovery.md) - the write boundary and receipts.
- [Platform](../04-connect/02-platform.md) - approvals and events.
- [Stores](../04-connect/01-stores.md) - persistence.
- [Decision contract](../../02-decision/01-contract/01-decision-contract.md) - the decision shape.
