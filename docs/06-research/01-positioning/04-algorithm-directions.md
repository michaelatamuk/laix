# Algorithm directions

**Status:** research memo. All four directions now have a deterministic prototype; none is a novelty
claim yet. Each one still needs a prior-art check, a formal statement and a benchmark before it can
be described as a new algorithm.

The current LAIX contribution is a decision contract and a composition of standard scoring rules.
This page records four directions that could give LAIX an algorithm of its own.

## Implementation status

| Direction | Prototype | API | Docs |
|---|---|---|---|
| CA-VOD | one-step value of decision plus optional belief-state future value | `CAVODPlanner` | [Algorithm prototypes](../../02-core/03-planning/05-algorithm-prototypes.md) |
| AADS | index policy for human attention | `AttentionScheduler` | [Algorithm prototypes](../../02-core/03-planning/05-algorithm-prototypes.md) |
| CDR | greedy minimum-cost repair | `repair_continuity` | [Algorithm prototypes](../../02-core/03-planning/05-algorithm-prototypes.md) |
| CDA | linear counterfactual attribution | `counterfactual_attribution` | [Algorithm prototypes](../../02-core/03-planning/05-algorithm-prototypes.md) |

The prototypes are deterministic and training-free. They are first implementations, not the full
research methods described below.

## 1. What is novel today

The current implementation is transparent and deterministic. It is not built on a new optimizer or
a new learning rule.

| Component | Current method | Location |
|---|---|---|
| Utility | linear weighted sum with simple risk transforms | `core/engines/planners/utility/utility_model.py` |
| Commitment | weighted sum of fulfil, violate, due, blocked and create | `core/engines/planners/commitment/commitment_planner.py` |
| Execution risk | linear penalties for irreversibility, unknown risk, approval and recovery | `core/engines/planners/execution/execution_planner.py` |
| Human attention | linear penalties plus a budget check | `core/engines/planners/human_attention/human_attention_planner.py` |
| Composite | additive total of the four terms with fixed weights | `core/engines/live/live_composite_planner.py` |
| Confidence | gap heuristic: `0.5 + 0.5 * (gap / best)` | the planner classes |
| Calibration | reliability bins over confidence | `core/engines/learning/decision_calibration.py` |
| Learning | UCB bandit | `core/engines/policies/implementations/bandit.py` |

The real novelty is in the representation and the contract:

- one decision shape for act, ask, wait, verify and escalate;
- commitments, execution risk and human attention in one scored decision;
- decision continuity;
- a model-optional `PlannerPolicy`;
- Python/TypeScript parity, conformance and a decision record.

That is systems and representation novelty. It is not algorithmic novelty.

## 2. What would count as a new algorithm

A defensible claim needs four things:

1. **A new problem formulation.** The problem must be stated more precisely than "combine four
   scores." It should expose a decision structure that existing methods do not handle.
2. **A new algorithm or a materially new adaptation.** A weighted sum with new names is not enough.
3. **Evidence.** A proof, a guarantee, or a strong empirical result against credible baselines.
4. **A benchmark others can run.** The result must be reproducible and comparable.

The best opportunity is not another model. It is a new decision problem: **commitment- and
attention-constrained decisions with continuity**.

## 3. Candidate 1: Commitment-Attention Value of Decision (CA-VOD)

**Problem.** Choose among act, ask, wait, verify and escalate when the next action changes
commitments, consumes human attention, carries execution risk and changes what can be decided next.

**State.** A finite-horizon constrained POMDP:

```text
s = (belief, commitments, approvals, attention_budget, receipts, outcomes)
```

- `belief`: uncertainty over the task state and action outcomes;
- `commitments`: open promises, deadlines and dependencies;
- `approvals`: pending, approved or rejected;
- `attention_budget`: remaining human attention;
- `receipts` and `outcomes`: what the host reported and what happened.

**Actions.** The five verbs, applied to the host's options:

```text
act(o) | ask(o) | wait | verify(o) | escalate(o)
```

**Transitions.** Each action updates the task belief, commitment lifecycle, approval state,
attention budget and receipt state. `ask` and `verify` add information value; `wait` preserves the
option to act later; `act` may be irreversible.

**Objective.** Maximise expected utility minus execution risk and attention cost, subject to hard
commitments, approvals and the attention budget:

```text
maximise    E[ sum_t gamma^t R(s_t, u_t, s_{t+1}) ]
subject to  hard commitments, approvals, attention budget
```

**Algorithm.** Start with a one-step lookahead with value of information, backed by rollout or
point-based value iteration:

```text
V(u) = E[R(s, u, s')] + gamma * E[V(s')]
```

For `ask` and `verify`, include the expected improvement in the next decision minus attention and
delay. For `wait`, include the option value of acting later. For `act`, include irreversible risk
and commitment effects.

**Novelty hypothesis.** Value of information and POMDPs are old. The new formulation is
**commitment- and attention-aware value of information over the five agent decision verbs, with
continuity**. That is the claim to test.

**Experiment.**

- Baselines: current weighted sum; POMDP without commitments; VOI without attention;
  commitment-aware but attention-blind; oracle on small cases.
- Metrics: decision accuracy, commitments kept, attention spent, irreversible actions, calibration
  and latency.
- Cases: the existing LAIX benchmark plus new commitment, attention and continuity cases.

**Effort:** high. **Fit:** core. **Priority:** first.

## 4. Candidate 2: Attention-Aware Decision Scheduling (AADS)

**Problem.** Many agents compete for the same humans. The question is not only whether one decision
should ask, but which pending decision should receive human attention now, which should wait, and
which should be batched.

**Model.** A restless multi-armed bandit. Each pending decision has:

- risk;
- commitment deadline;
- information value;
- waiting cost;
- attention cost if reviewed;
- probability that review changes the action.

The state of each decision evolves while it waits. The budget is the available human attention.

**Algorithm.** Use a Whittle index or a linear-programming relaxation for the restless bandit. The
index ranks pending decisions by the marginal value of reviewing them now.

**Novelty hypothesis.** Per-action approvals exist. **Fleet-level attention scheduling for agent
decisions with commitments, deadlines and risk** is a different problem. It creates a capability
that per-action runtimes do not have: not just allow or block, but who gets the human now.

**Experiment.** Queue simulation plus real traces. Metrics: commitments kept, risk exposure,
attention utilisation, time-to-decision and review throughput.

**Effort:** medium-high. **Fit:** app kit. **Priority:** second.

## 5. Candidate 3: Continuity Decision Repair (CDR)

**Problem.** Continuity today is state carry-forward. It does not detect when a new decision
contradicts an earlier commitment, approval or receipt. A continuity algorithm would maintain a
consistent decision history and repair it at minimum cost.

**Model.** A decision graph:

- nodes: decisions, commitments, approvals, receipts and outcomes;
- edges: supports, conflicts and dependencies.

When new evidence arrives, find the minimal-cost revision set that restores consistency.

**Algorithm.** Incremental truth maintenance plus weighted MaxSAT or ILP:

1. identify the conflict;
2. compute minimal revisions;
3. price each revision by utility loss, attention cost, approval cost and commitment violation;
4. choose the cheapest repair.

**Novelty hypothesis.** Decision continuity is usually state passing or event sourcing.
**Commitment-aware minimal repair of an agent decision history** is a different algorithmic problem.

**Experiment.** Synthetic sequences with contradictions, late receipts, rejected approvals and
expired commitments. Metrics: repair cost, stability, consistency and explanation length.

**Effort:** medium. **Fit:** core and app kit. **Priority:** third.

## 6. Candidate 4: Counterfactual Decision Attribution (CDA)

**Problem.** When LAIX chooses ask instead of act, the current rationale is a score breakdown. A
stronger algorithm would answer: which input, commitment, attention cost or risk value actually
caused the decision, and what is the smallest change that would have produced a different verb?

**Model.** Search for the minimal counterfactual change that flips the verb. For linear and weighted
decisions this is a small MILP. For rule-based decisions it is a search over constraint relaxations.
For sequences, use Shapley attribution over the decision trajectory.

**Novelty hypothesis.** Counterfactual explanations exist. **Counterfactual attribution for
commitment- and attention-aware agent decisions, across a continuity sequence**, is new and directly
useful for audit.

**Experiment.** Validity, minimality, stability and human usefulness. The last one needs a small
study with auditors or operators.

**Effort:** medium. **Fit:** audit and explainability. **Priority:** fourth.

## 7. Priority

| Direction | Layer | Novelty | Effort | First evidence |
|---|---|---|---|---|
| **CA-VOD** | core | high | high | weighted-sum baseline plus new benchmark cases |
| **AADS** | app kit | high | medium-high | queue simulation plus traces |
| **CDR** | core/app kit | medium | medium | synthetic continuity sequences |
| **CDA** | audit | medium | medium | counterfactual validity plus a small user study |

Recommended order:

1. **CA-VOD** first: it replaces the weighted sum and gives the core a real decision algorithm.
2. **AADS** second: it creates a new fleet-level capability and a clear algorithmic contribution.
3. **CDR** third: it makes continuity a real consistency problem rather than state passing.
4. **CDA** fourth: it turns the decision record into causal, audit-ready explanations.

## 8. Prior art to check

Before claiming novelty, check these areas:

- POMDPs, value of information and optimal stopping;
- constrained MDPs and safe reinforcement learning;
- restless bandits and Whittle indices;
- human-in-the-loop review scheduling and queueing;
- truth maintenance, belief revision and model-based diagnosis;
- counterfactual explanations and Shapley attribution;
- commitment-based agent architectures and social commitments;
- decision intelligence platforms and business rules engines.

The claim must survive a direct comparison with these lines of work. A new name is not a new method.

## 9. Next step

The deterministic prototypes are in
[Algorithm prototypes](../../02-core/03-planning/05-algorithm-prototypes.md), and the smoke results
are in [Algorithm prototype results](../02-evaluation/algorithm-prototypes.md).

The one-step and belief-state future-value versions are in place. The next step is the constrained
research version:

- encode hard commitments and the attention budget in the transition model;
- keep the deterministic fallback for low latency;
- add baselines and ablations;
- expand the cases beyond the smoke tests;
- run the prior-art check again.

Only after that should this page describe CA-VOD as an invented algorithm.
