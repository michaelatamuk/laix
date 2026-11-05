# Glossary

| Term | Meaning |
|---|---|
| **Request** | One `DecisionRequest`: the situation, signals, options and limits the app supplies. |
| **Decision** | The one response shape: verb, confidence, reason, rationale, action, approval, target and trail. |
| **Verb** | `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| **Policy** | A callable with `decide(request)` that returns decisions. |
| **Engine** | A planner behind `EnginePolicy`; it returns a `Plan`, and the policy converts it to a `Decision`. |
| **Plan** | An engine's answer: verb, confidence, reason, action, score and alternatives. |
| **Target** | Who receives a decision: `one`, `some`, `all`, `peer` or `gather`. |
| **Stream** | A `StreamSession` that applies event time, cadence, backpressure and revisions to many requests. |
| **Checkpoint** | A resumable snapshot of a stream. |
| **Commitment** | A promised step with a due time, status and dependencies. |
| **Outcome** | A measured result of a decision, with a label and attribution. |
| **Causal effect** | An estimate of the effect of one arm against another. |
| **Calibration** | A comparison between stated confidence and observed accuracy. |
| **Receipt** | What the host returned after trying to execute or deliver a decision. |
| **Record** | The auditable lifecycle of a decision: draft, approve, reject, execute, undo, verify. |
| **Host** | The application that owns data, UI, execution, storage and delivery. |
| **App kit** | The optional LAIX layer around the core: runtime, streaming, execution, stores, platform and bench. |
