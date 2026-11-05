# Glossary

| Term | Meaning |
|---|---|
| **Request** | One `DecisionRequest`: the situation, signals, options and limits the app supplies. |
| **Signal** | One item that might need attention, such as a deadline or a risk. |
| **Situation** | The current state: what is believed, what the goal is and what actions exist. |
| **Decision** | The one response shape: verb, confidence, reason, rationale, action, approval, target and trail. |
| **Verb** | `wait`, `observe`, `guide`, `ask`, `act`, `verify` or `escalate`. |
| **Policy** | A callable with `decide(request)` that returns decisions. |
| **Adapter** | App code that turns app events into requests and decisions into app actions. |
| **Attention** | The mechanism that ranks signals and decides whether to surface, hold, act or escalate. |
| **Attention-aware planning** | Planning that treats interruption, approval and escalation as a budget. |
| **Attention budget** | The interruption and approval capacity a task may spend. |
| **Planner** | A solver that returns a `Plan`: utility, MDP, POMDP or an external planner. |
| **Engine** | The code contract for a planner: `DecisionEngine.solve(problem) -> Plan`; `EnginePolicy` wraps it. |
| **Plan** | A planner's answer: verb, confidence, reason, action, score and alternatives. |
| **MDP** | A model with states, actions, transitions, rewards, discount and horizon; the planner chooses the best action. |
| **POMDP** | An MDP with hidden state; the planner keeps a belief over states and updates it from observations. |
| **Optimality gap** | The difference between a planner's reward and the best reward available in the model. |
| **Risk attitude** | How a planner trades expected value against variance: `neutral`, `averse` or `seeking`. |
| **Limits** | Risk, approval, safety and policy constraints that bound a decision; a gate, not a module. |
| **Commitment** | A promised step with a due time, status and dependencies. The planning layer tracks commitments. |
| **Commitment-aware planning** | Planning with promises, due times and dependencies in the state. |
| **Recovery** | Run steps in order and undo the completed ones when a later step fails. |
| **Execution-aware planning** | Planning with reversibility, unknown outcomes, approval and recovery cost. |
| **Saga** | The pattern behind recovery: a multi-step action with an undo for each step. |
| **Target** | Who receives a decision: `one`, `some`, `all`, `peer` or `gather`. |
| **Stream** | A `StreamSession` that applies event time, cadence, backpressure and revisions to many requests. |
| **Checkpoint** | A resumable snapshot of a stream. |
| **Decision timeline** | An append-only record of decisions with revision and event-time rules. |
| **Live decision bench** | A training-free comparison of planners on risk, promise, execution and attention cases. |
| **TTL** | Time to live: how long state or a decision stays valid. |
| **SSE** | Server-sent events: a one-way HTTP stream of events. |
| **NDJSON** | Newline-delimited JSON: one event per line. |
| **Outcome** | A measured result of a decision, with a label and attribution. |
| **Causal effect** | An estimate of the effect of one arm against another. |
| **Causal attribution** | Assigning part of an outcome to a decision or arm rather than to other factors. |
| **Bandit** | A learner that chooses among arms and updates from rewards. |
| **Ledger** | A store of measured outcomes or commitments. |
| **UCB** | Upper confidence bound: choose the arm with the best reward plus a bonus for arms tried less. |
| **Calibration** | A comparison between stated confidence and observed accuracy. |
| **Decision calibration** | Comparing stated confidence with whether the chosen verb and action were correct. |
| **Calibrated policy** | A policy wrapper that applies a decision calibration report to every decision. |
| **JEV** | A typed decision model from TypeSafe; it returns a judgment and can sit behind a LAIX policy. |
| **LLM** | Large language model: a model that generates or judges text. |
| **PPMA** | The layer above LAIX that owns activation, commit and the system-level loop; LAIX decides inside one task. |
| **Conformance** | Comparing LAIX decisions with the shared vectors to confirm behaviour matches. |
| **Receipt** | What the host returned after trying to execute or deliver a decision. |
| **Record** | The auditable lifecycle of a decision: draft, approve, reject, execute, undo, verify. |
| **Port** | An interface the host implements; LAIX calls it and the host supplies the behaviour. |
| **Platform** | The host system below LAIX: skills, events and approvals. |
| **Host** | The application that owns data, UI, execution, storage and delivery. |
| **App kit** | The optional LAIX layer around the core: runtime, streaming, execution, stores, platform and bench. |
