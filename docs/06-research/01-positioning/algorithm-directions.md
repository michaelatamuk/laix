# Algorithm directions

**Status:** research memo. The four original directions and the new sequence family now have a
deterministic prototype; none is a novelty claim yet. Each one still needs a prior-art check, a
formal statement and a benchmark before it can be described as a new algorithm.

The current LAIX contribution is a decision contract and a composition of standard scoring rules.
This page records five directions that could give LAIX an algorithm of its own.

## Implementation status

| Direction | Prototype | API | Docs |
|---|---|---|---|
| CA-VOD | one-step value of decision plus optional belief-state future value | `CAVODPlanner` | [Decision value](../../02-decision/03-decision-shapes/01-single/04-decision-value.md) |
| AADS | index policy plus exact single-arm Whittle index | `AttentionScheduler`, `WhittleScheduler` | [Fleet attention](../../02-decision/03-decision-shapes/03-fleet.md) |
| CDR | greedy and exact minimum-weight vertex cover | `repair_continuity` | [Decision history](../../02-decision/03-decision-shapes/04-history.md) |
| CDA | linear attribution plus bounded counterfactual search | `counterfactual_attribution`, `counterfactual_search` | [Explain a decision](../../02-decision/03-decision-shapes/05-explain.md) |
| CABB | exact finite-horizon branch and bound over commitments and attention | `CABBPlanner`, `RolloutPlanner`, `ReplanPlanner` | [Sequence planning](../../02-decision/03-decision-shapes/02-sequence.md) |

The prototypes are deterministic and training-free. They are first implementations, not the full
research methods described below.

## 1. What is novel today

The current implementation is transparent and deterministic. It is not built on a new optimizer or
a new learning rule.

| Component | Current method | Location |
|---|---|---|
| Utility | linear weighted sum with simple risk transforms | `decision/planners/single/utility/utility_model.py` |
| Commitment | weighted sum of fulfil, violate, due, blocked and create | `decision/planners/single/commitment/commitment_planner.py` |
| Execution risk | linear penalties for irreversibility, unknown risk, approval and recovery | `decision/planners/single/execution/execution_planner.py` |
| Human attention | linear penalties plus a budget check | `decision/planners/single/human_attention/human_attention_planner.py` |
| Composite | additive total of the four terms with fixed weights | `decision/planners/single/composite/live_composite_planner.py` |
| Confidence | gap heuristic: `0.5 + 0.5 * (gap / best)` | the planner classes |
| Calibration | reliability bins over confidence | `decision/learning/calibration/decision_calibration.py` |
| Learning | UCB bandit | `decision/policies/implementations/bandit.py` |

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

**Effort:** high. **Fit:** decision. **Priority:** first.

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
that per-action decision layers do not have: not just allow or block, but who gets the human now.

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

**Effort:** medium. **Fit:** decision and app kit. **Priority:** third.

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

## 7. Candidate 5: Commitment-Attention Branch and Bound (CABB)

**Problem.** Choose a whole chain of decisions over a known horizon, not one decision at a time.
Every step consumes a shared human-attention budget and may fulfil or violate an open commitment. A
choice that looks best now can block a better choice later.

**Model.** A finite deterministic sequence:

```text
steps = (S_1, ..., S_T),  S_t = {options at time t}
state = (commitment statuses, remaining attention)
score(chain) = sum_t immediate(t) - terminal_open_penalty
```

**Algorithm.** Branch and bound with two admissible bounds:

- a relaxed per-step score bound;
- a terminal promise bound for commitments still open at the end.

The search returns the exact best chain for the supplied finite scenario.

**Guarantee.** For the supplied deterministic scenario, the returned chain is optimal. This is not a
guarantee for an uncertain or infinite-horizon environment.

**Novelty hypothesis.** Branch and bound is old. The candidate is the problem formulation:
**exact finite-horizon commitment- and attention-constrained sequence planning over the five agent
decision verbs**. The prior-art check must decide whether the formulation is new, not whether branch
and bound is new.

**Experiment.**

- Baselines: greedy one-step, greedy rollout, brute force on small cases.
- Metrics: optimality, decision quality, nodes and wall time.
- Cases: small deterministic scenarios plus the attention tradeoff case where greedy fails.

**Prototype result.** On 12 synthetic 4-step/3-option scenarios, CABB matches brute force on 12/12
and rollout on 10/12. In the attention tradeoff case, CABB scores `1.105` against rollout `0.605`
because it saves attention for a later high-value option. This shows decision quality, not speed:
the bound is still loose on tiny cases.

**Effort:** high. **Fit:** decision. **Priority:** first for algorithmic novelty.

## 8. Priority

| Direction | Layer | Novelty | Effort | First evidence |
|---|---|---|---|---|
| **CABB** | decision | high (candidate) | high | exact optimality on small scenarios plus the greedy tradeoff case |
| **CA-VOD** | decision | high | high | weighted-sum baseline plus new benchmark cases |
| **AADS** | app kit | high | medium-high | queue simulation plus traces |
| **CDR** | decision/app kit | medium | medium | synthetic continuity sequences |
| **CDA** | audit | medium | medium | counterfactual validity plus a small user study |

Recommended order:

1. **CABB** first for algorithmic novelty: it is the clearest new problem formulation and it has an
   exactness guarantee. The prior-art check decides whether the formulation is new.
2. **CA-VOD** second: it replaces the weighted sum and gives the decision layer a real decision algorithm.
3. **AADS** third: it creates a new fleet-level capability and a clear algorithmic contribution.
4. **CDR** fourth: it makes continuity a real consistency problem rather than state passing.
5. **CDA** fifth: it turns the decision record into causal, audit-ready explanations.

## 9. Prior art to check

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

## 10. Next step

The deterministic prototypes are in
[Decision pages](../../02-decision/03-decision-shapes/README.md), and the smoke results
are in [Algorithm prototype results](../02-evaluation/algorithm-prototypes.md).

The one-step, belief-state future-value and exact sequence prototypes are in place. The next step is
the research version:

- check prior art for commitment- and attention-constrained sequence planning;
- encode hard commitments and the attention budget in the transition model;
- keep the deterministic fallback for low latency;
- add baselines and ablations;
- expand the cases beyond the smoke tests;
- run the prior-art check again.

Only after that should this page describe CA-VOD or CABB as an invented algorithm.
