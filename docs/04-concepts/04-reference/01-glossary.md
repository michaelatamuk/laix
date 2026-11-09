# Glossary

The vocabulary is grouped by where the term lives. The pages linked in each section define the
contracts in detail.

## Core records

| Term | Meaning |
|---|---|
| **Request** | One `DecisionRequest`: the subject, moment, signals or situation, options and limits the app supplies. |
| **Signal** | One item that might need attention, such as a deadline, risk or change. |
| **SignalContext** | The signal-side input: current time, quiet hours, interruption budget and other ambient facts. |
| **Situation** | The action-side input: what is believed, what the goal is, the options and the constraints. |
| **Option** | One `ActionOption`: an id, a verb, a name, expected benefit, cost, risk and reversibility. |
| **Constraint** | A hard or soft limit on the choice, such as risk, approval, safety, cost or latency. |
| **Belief** | A proposition with a confidence, evidence and optional expiry. |
| **Goal** | A desired outcome for the task. |
| **Observation** | A measured fact with a source, confidence, cost and latency. |
| **Decision** | The one response shape: verb, confidence, reason, rationale, action, approval, target and trail. |
| **Verb** | `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| **Reason code** | The stable branch key on a decision. App logic switches on it, not on `rationale`. |
| **Confidence** | How sure the decision is, with its source and calibration flag. |
| **Evidence** | An `EvidenceRef`: an id, kind, quote, source and optional confidence. |
| **Intent** | The structured action payload attached to a decision. |
| **Target** | Who receives the decision: `one`, `some`, `all`, `peer` or `gather`. |
| **Decision id** | The stable id of one decision. |
| **Trace** | The ordered events recorded around a decision. |

## Decision mechanisms

| Term | Meaning |
|---|---|
| **DecisionPolicy** | A chooser with `name` and `decide(request)`. It returns one or more decisions. |
| **Planner** | A strategy that scores the options and returns a `PlannerResult`. |
| **SequencePlanner** | A strategy that returns one `DecisionPlan` for a finite chain of decisions. |
| **DecisionScenario** | A finite chain: steps, commitments, attention budget and an open-commitment penalty. |
| **DecisionPlan** | The chosen action per step, score, attention spent, violations, node count and optimality. |
| **CompositePlanner** | A composition of planners that returns one `PlannerResult`; `LiveCompositePlanner` is the built-in composite planner. |
| **Protocol** | `Planner`: `solve(problem) -> PlannerResult`; `SequencePlanner`: `plan(scenario) -> DecisionPlan`. The protocol names the contract, not a component. |
| **PlannerResult** | A planner's internal answer: verb, confidence, reason, action, score and alternatives. |
| **PlannerInput** | The planner input: subject, moment, situation, options, signals, context and attributes. |
| **Composite score** | The four terms `LiveCompositePlanner` combines for one option: utility, commitment, execution and human attention. |
| **Live composite planner** | `LiveCompositePlanner`: the composite planner that turns the four planner scores into one `PlannerResult`. |
| **Attention** | The shared idea: what deserves a person's limited time. Two mechanisms use it: signal attention and human-attention planning. |
| **Signal attention** | The gate pipeline in `core/engines/sensing/signals/` that ranks signals and returns `guide`, `wait`, `act` or `escalate`. |
| **Human-attention planning** | `HumanAttentionPlanner`: pricing interruption, approval and escalation when choosing an action. |
| **Human-attention budget** | The interruption and approval capacity a task may spend; HumanAttentionBudget. |
| **Signal interruption budget** | A per-cycle cap on delivered signal decisions, set by `SignalContext.signal_interruption_budget`. |
| **Resource budget** | Compute, latency and sensing capacity, managed by `ResourceScheduler`; distinct from the human-attention budget. |
| **Decision class** | One of the ten request/policy shapes: signal attention, action, active perception, safety, replanning, allocation, negotiation, preference, verification and escalation. |
| **Shadow policy** | A wrapper that returns the primary decision and records where the shadow policy disagrees. |
| **Group policy** | The policy that sets target and recipients and masks private fields before sharing. |

## State, continuity and execution

| Term | Meaning |
|---|---|
| **Commitment** | A promised step with a due time, status and dependencies. |
| **Ledger** | A store of measured outcomes or commitments. |
| **Stream** | A `StreamSession` that applies event time, cadence, backpressure and revisions to many requests. |
| **Checkpoint** | A resumable snapshot of a stream. |
| **Decision timeline** | An append-only record of decisions with revision and event-time rules. |
| **Experience state** | `ExperienceState`: goals, phase, beliefs, observations and history for one live experience. |
| **Proposal** | The approval lifecycle for an action that needs a person: pending, approved, rejected, applied or undone. |
| **Approval** | The approval state on a decision record: required, state, approver, time and note. |
| **Decision record** | The audit lifecycle of a decision: draft, approved, rejected, executed or undone. |
| **Audit event** | One append-only event on a decision record. |
| **Undo** | Whether a decision record can still be reversed, and how. |
| **Receipt** | What the host returned after trying to execute a decision. |
| **Delivery receipt** | What the delivery port returned: decision, channel, status and detail. |
| **Outcome** | A measured result of a decision, with a label and attribution. |
| **TTL** | Time to live: how long state or a decision stays valid. |
| **Saga** | A multi-step action with an undo for each step; completed steps are compensated in reverse. |
| **Port** | An interface the host implements; LAIX calls it and the host supplies the behaviour. |
| **Platform** | The host system below LAIX: skills, events and approvals. |
| **Delivery** | The port and receipt for sending a decision through a channel. |

## Learning and evidence

| Term | Meaning |
|---|---|
| **Bandit** | A learner that chooses among arms and updates from rewards. |
| **UCB** | Upper confidence bound: choose the arm with the best reward plus a bonus for arms tried less. |
| **Causal effect** | An estimate of the effect of one arm against another. |
| **Causal attribution** | Assigning part of an outcome to a decision or arm, separate from other factors. |
| **Calibration** | A comparison between stated confidence and observed accuracy. |
| **Decision calibration** | Comparing stated confidence with whether the chosen verb and action were correct. |
| **Calibrated policy** | A policy wrapper that applies a decision calibration report to every decision. |
| **Model learning** | Updating a model from measured transitions or outcomes. |
| **Case** | One request and the decision it should produce in an evaluation or bench. |
| **Suite** | A group of cases for one decision class. |
| **Agreement** | The share of cases that produced the expected decision. |
| **Conformance** | Comparing LAIX decisions with the shared vectors to confirm behaviour matches. |
| **Vector** | A fixed input and its expected output, used as a conformance test. |
| **Bench** | A deterministic set of cases, suites and reports. |

## Host and product

| Term | Meaning |
|---|---|
| **Core** | The stateless decision package: contract, domain records, decision engines, sensing, learning, evaluation and support. |
| **Domain** | The records and state layer: decisions, commitments, outcomes and perception. |
| **Engine** | The processing layer: decision, sensing, learning and evaluation. |
| **App kit** | The optional LAIX layer around the core: decision loop, streaming, execution, stores, platform and bench. |
| **DecisionClient** | The app-kit one-decision surface. |
| **Decision loop** | `DecisionRuntime`: the app-kit loop that links observation, state, policy, execution and outcome. |
| **Host** | The application that owns data, UI, execution, storage and delivery. |
| **Live** | A decision made inside the running loop, at event time, with the current state. |
| **JEV** | A typed decision model from TypeSafe; it returns a judgment and can sit behind a LAIX policy. |
| **LLM** | Large language model: a model that generates or judges text. |
| **PPMA** | The layer above LAIX that owns activation, commit and the system-level loop; LAIX decides inside one task. |

The full contracts are in [Core overview](../../02-core/README.md) and
[App-kit overview](../../03-appkit/README.md).
