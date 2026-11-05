# Decision engine contract

The engine contract, the built-in engines and the simulator are implemented in
`core/engines/`. The layer stays usable without any engine: rule policies and the
packaged policies still return the same decision shape.

The goal is:

- one engine contract;
- LAIX’s own engines;
- adapters for external engines;
- every engine returns the same `Plan`; the adapter returns the same `Decision` and uses the same
  lifecycle.

## Architecture

```text
DecisionRequest
      │
      ▼
   Policy
   ├── rule policy              today
   └── EnginePolicy             wraps any engine
          ├── external engine   JEV, OR-Tools, a POMDP library
          └── LAIX engine       UtilityEngine, MDPEngine, POMDPEngine
      │
      ▼
   Decision
      │
      ▼
approval -> execute -> verify -> outcome
```

The rule:

> An engine produces a plan. The layer turns that plan into a decision. All paths return the same
> decision shape.

## Core contracts

```python
from laix import DecisionProblem, EnginePolicy, Plan

class DecisionEngine(Protocol):
    def solve(self, problem: DecisionProblem) -> Plan: ...

policy = EnginePolicy(engine)
decision = policy.decide(request)[0]
```

`EnginePolicy` owns the conversion; the engine returns a `Plan`, the policy returns
the one `Decision` shape.

The contracts:

| Contract | Purpose |
|---|---|
| `DecisionProblem` | states, actions, utility, limits and uncertainty |
| `Plan` | chosen option, expected value, confidence and alternatives |
| `DecisionEngine` | `solve(problem) -> Plan` |
| `EnginePolicy` | turns a plan into a `Decision` |
| `UtilityEngine` | expected utility with hard limits and risk attitude |
| `MdpModel`, `MDPEngine` | finite MDP, value iteration and a greedy plan |
| `PomdpModel`, `POMDPEngine` | belief update and finite-horizon planning |
| `Simulator` | runs an engine in a model |
| `SimulationReport` | engine comparison, reward and optimality gap |
| `CalibrationReport` | predicted confidence vs observed accuracy |
| `ModelLearner` | transition and reward learning with rollback |

## Capabilities

| # | Capability | Piece |
|---|---|---|
| 1 | State and uncertainty | `StateEstimate`, distributions, observation model |
| 2 | Option model | `ActionEffect`, preconditions, costs, transitions |
| 3 | Utility model | `UtilityModel`, weights, risk attitude, constraints |
| 4 | Planning | `DecisionEngine.solve(problem) -> Plan` |
| 5 | Calibration | reliability report and confidence adjustment |
| 6 | Learning | `ModelLearner` for transitions and utilities |
| 7 | Explanation | chosen plan, alternatives, expected value |
| 8 | Simulator and bench | optimality gap and engine comparison |

## Path A: external engine

```python
decision = decide(request, policy=EnginePolicy(JevEngine(...)))[0]
decision = decide(request, policy=EnginePolicy(OrToolsEngine(...)))[0]
decision = decide(request, policy=EnginePolicy(MDPEngine(...)))[0]
```

The external engine can be a classifier, an optimizer, a planner or a model service. The adapter maps
its output into a `Plan`.

## Path B: LAIX engine

```python
class MDPEngine:
    def solve(self, problem: DecisionProblem) -> Plan:
        ...
        return Plan(
            verb="act",
            action_id="valve",
            confidence=0.88,
            reason_code="expected_utility",
            rationale="the valve plan has the highest expected utility",
            score=0.91,
            alternatives=(...),
        )

decision = decide(request, policy=EnginePolicy(MDPEngine()))[0]
```

A convenience constructor is intentionally not added: pass the engine through
`EnginePolicy(engine)` so every path shares one conversion.

Internally this is still an engine-backed policy.

## Design rules

1. Every engine returns a `Plan`; `EnginePolicy` returns the one `Decision` shape.
2. Approval, execution, verification and outcome recording stay outside the core.
3. The app supplies the domain model. LAIX supplies the decision method.
4. Engines are optional. The rule policies remain.
5. An engine can be replaced without changing the app adapter.
6. A planner result must be explainable: chosen plan, alternatives, expected value.
7. Bench compares engines on the same cases.

## Build order

### 1. Engine contract

- [x] `DecisionProblem`
- [x] `Plan`
- [x] `DecisionEngine`
- [x] `EnginePolicy`
- [x] `to_problem` and `to_decision`

### 2. Utility and constraint engine

- [x] expected utility
- [x] hard constraints
- [x] risk attitude
- [x] explanation
- [x] tests against the existing action policy

### 3. MDP planner

- [x] states, actions and transitions
- [x] discount and horizon
- [x] known-optimal bench cases
- [x] optimality gap report

### 4. Simulator and bench

- [x] `Simulator`
- [x] seeded scenarios
- [x] seeded stochastic rollouts
- [x] engine comparison
- [x] engine bench CLI (`--engines`)
- [x] regression cases

### 5. Calibration

- [x] predicted vs observed confidence
- [x] per-policy report
- [x] confidence adjustment

### 6. Model learning

- [x] learn transitions and rewards from outcomes
- [x] keep the UCB bandit as a simple learner
- [x] rollback when a learned model gets worse
- [x] export a learned model as an `MdpModel`

### 7. POMDP

- [x] observation model
- [x] observation model required for every reachable state/action pair
- [x] belief update
- [x] small solver
- [x] benchmark against the MDP path
- [x] `compare_pomdp_to_mdp` diagnostic

### 8. TypeScript parity

- [x] engine contracts
- [x] `EnginePolicy`
- [x] utility engine
- [x] MDP engine
- [x] simulator and bench

## Limits

- A planner needs a world model. The app supplies the domain transitions; LAIX plans over them.
- Utility elicitation remains the hard part.
- POMDPs get expensive quickly.
- Calibration needs real outcomes.
- Planner explanations are harder than rule traces.
- The API grows. Keep every piece optional.

## Current state

| Piece | Status |
|---|---|
| Rule policies | done |
| UCB bandit | done |
| Bench | done |
| Engine contract | done |
| Utility engine | done |
| MDP planner | done |
| Simulator and engine comparison | done |
| Engine bench CLI | done |
| Calibration | done |
| Model learning | done |
| POMDP | done |
| TypeScript parity: contract, `EnginePolicy`, utility, MDP, simulator | done |

Calibration, model learning and POMDP are Python-first. Their contracts are small and can be
ported when a TypeScript host needs them.
