# Platform

The app describes the experience. The platform runs work and reports results. LAIX decides; the
platform executes.

| Word | Meaning |
|---|---|
| **Platform** | The system below LAIX that runs skills, approvals, state and events. |
| **Skill** | A named unit of work the platform can run. |
| **Capability level** | How much power a call needs: `fast`, `balanced` or `deep`. |

## Contract

```python
from laix import ApprovalRequest, SkillCall

class MyPlatform:
    def run_skill(self, call: SkillCall): ...
    def cancel(self, run_id: str, reason: str = "") -> bool: ...
    def request_approval(self, request: ApprovalRequest): ...
    def read_state(self, key: str): ...
    def write_state(self, key: str, value): ...
    def events(self, trace_id: str): ...
    def capability(self, level: str): ...
```

| Method | Purpose |
|---|---|
| `run_skill` | Run a named skill. |
| `cancel` | Stop a running step. |
| `request_approval` | Ask a person. |
| `read_state` / `write_state` | Keep session state. |
| `events` | Return events for a trace. |
| `capability` | Return a capability level. |

## Records

| Record | Fields | Meaning |
|---|---|---|
| `SkillCall` | `capability`, `args`, `trace_id` | One named skill call. |
| `ApprovalRequest` | `decision_id`, `action_name`, `rationale`, `risk`, `reversible`, `evidence` | What the platform is asked to approve. |
| `ApprovalDecision` | `approved`, `by`, `at`, `note` | What the approver decided. |
| `Capability` | `level`, `modalities`, `max_latency_ms`, `max_cost` | A capability level, not a model name. |
| `PlatformEvent` | `trace_id`, `kind`, `at`, `payload` | One event streamed back for a trace. |

`CAPABILITY_LEVELS = ("fast", "balanced", "deep")` is exported for validation.

## Approval flow

1. A decision sets `requires_approval`.
2. The bridge builds an `ApprovalRequest` with the decision, action, risk, reversibility and evidence.
3. The platform asks a person and returns an `ApprovalDecision`.
4. The bridge continues only when `approved` is true.
5. The approval and the result are recorded on the execution and the audit trail.

The execution lifecycle is in [Execution and recovery](../03-execute/01-execution-and-recovery.md).
The proposal lifecycle is in [Proposals and records](../03-execute/02-proposals-and-records.md).

## Example

```python
from laix import InMemoryPlatform, SkillCall

platform = InMemoryPlatform()
platform.register("lookup", lambda call: {"value": 7})

result = platform.run_skill(SkillCall("lookup", {}, trace_id="tr-1"))
events = platform.events("tr-1")
print(result, list(events))
```

`InMemoryPlatform` is an in-memory implementation. A real adapter wraps an agent runtime, a cloud
platform or another system.

## Adapter guidance

- Keep skills named by capability, not by vendor.
- Keep credentials and authorization in the platform.
- Return a stable result shape and a trace id.
- Make `cancel` idempotent.
- Make `request_approval` blocking or return a pending decision; do not pretend approval happened.
- Do not put raw customer data in `PlatformEvent.payload`.

## TypeScript

TypeScript exports `Platform`, `InMemoryPlatform`, `SkillCall`, `ApprovalRequest`, `ApprovalDecision`,
`Capability`, `CAPABILITY_LEVELS` and `PlatformEvent`. The input and state types are `ApprovalInput`,
`ApprovalState` and `CapabilityLevel`; `UndoInput` is used by the audit surface.

## Boundary

- The platform owns skills, credentials, approvals, session state and events.
- LAIX owns the decision, the approval requirement, the execution lifecycle and the receipt.
- A platform adapter is not a decision policy; it only runs work and reports results.

## Related

- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the bridge and receipts.
- [Proposals and records](../03-execute/02-proposals-and-records.md) - approval and audit.
- [Delivery](03-delivery.md) - the output channel.
- [Deployment](../05-operate/03-deployment.md) - security and reliability.
