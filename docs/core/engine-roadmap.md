# Decision engine roadmap

This page describes the next major step for LAIX: adding a real decision-engine core while keeping
LAIX usable as a decision layer.

The goal is:

- one engine contract;
- LAIX’s own engines;
- adapters for external engines;
- every engine returns the same `Decision` and uses the same lifecycle.

## Architecture

```text
DecisionRequest
      │
      ▼
   Policy
   ├── rule policy              today
   ├── EnginePolicy             wraps any engine
   │      └── external engine   JEV, OR-Tools, a POMDP library
   └── BuiltInEnginePolicy      uses a LAIX engine
          └── DecisionEngine    LAIX planner
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
class DecisionEngine(Protocol):
    def solve(self, problem: DecisionProblem) -> Plan: ...

class EnginePolicy:
    def __init__(self, engine: DecisionEngine):
        self.engine = engine

    def decide(self, request):
        problem = to_problem(request)
        plan = self.engine.solve(problem)
        return [to_decision(plan)]
```

The contracts to add:

| Contract | Purpose |
|---|---|
| `DecisionProblem` | states, actions, utility, limits and uncertainty |
| `Plan` | chosen action, expected value, confidence and alternatives |
| `DecisionEngine` | `solve(problem) -> Plan` |
| `EnginePolicy` | turns a plan into a `Decision` |
| `Simulator` | runs a policy in a model and returns outcomes |
| `CalibrationReport` | predicted confidence vs observed accuracy |

## Capabilities

| # | Capability | Piece |
|---|---|---|
| 1 | State and uncertainty | `StateEstimate`, distributions, observation model |
| 2 | Action model | `ActionEffect`, preconditions, costs, transitions |
| 3 | Utility model | `UtilityModel`, weights, risk attitude, constraints |
| 4 | Planning | `DecisionEngine.solve(problem) -> Plan` |
| 5 | Calibration | reliability report and confidence adjustment |
| 6 | Learning | `ModelLearner` for transitions and utilities |
| 7 | Explanation | chosen plan, alternatives, expected value |
| 8 | Simulator and bench | optimality gap and engine comparison |

## Path A: external engine

```python
layer = Layer(policy=EnginePolicy(JevEngine(...)))
layer = Layer(policy=EnginePolicy(OrToolsEngine(...)))
layer = Layer(policy=EnginePolicy(MDPEngine(...)))
```

The external engine can be a classifier, an optimizer, a planner or a model service. The adapter maps
its output into a `Plan`.

## Path B: LAIX engine

```python
class MDPEngine:
    def solve(self, problem: DecisionProblem) -> Plan:
        ...
        return Plan(
            action_id="valve",
            expected_utility=0.91,
            confidence=0.88,
            alternatives=(...),
            explanation="...",
        )

layer = Layer(policy=EnginePolicy(MDPEngine()))
```

A convenience constructor may follow:

```python
layer = Layer(engine=MDPEngine())
```

Internally this is still an engine-backed policy.

## Design rules

1. Every engine returns a `Decision`.
2. Approval, execution, verification and outcome recording stay in the layer.
3. The app supplies the domain model. LAIX supplies the decision method.
4. Engines are optional. The rule policies remain.
5. An engine can be replaced without changing the app adapter.
6. A planner result must be explainable: chosen plan, alternatives, expected value.
7. Bench compares engines on the same cases.

## Build order

### 1. Engine contract

- [ ] `DecisionProblem`
- [ ] `Plan`
- [ ] `DecisionEngine`
- [ ] `EnginePolicy`
- [ ] `to_problem` and `to_decision`

### 2. Utility and constraint engine

- [ ] expected utility
- [ ] hard constraints
- [ ] risk attitude
- [ ] explanation
- [ ] tests against the existing action policy

### 3. MDP planner

- [ ] states, actions and transitions
- [ ] discount and horizon
- [ ] known-optimal bench cases
- [ ] optimality gap report

### 4. Simulator and bench

- [ ] `Simulator`
- [ ] seeded scenarios
- [ ] engine comparison
- [ ] regression cases

### 5. Calibration

- [ ] predicted vs observed confidence
- [ ] per-policy report
- [ ] confidence adjustment

### 6. Model learning

- [ ] learn transitions and utilities from outcomes
- [ ] keep the UCB bandit as a simple learner
- [ ] rollback when a learned model gets worse

### 7. POMDP

- [ ] observation model
- [ ] belief update
- [ ] small solver
- [ ] benchmark against the MDP path

### 8. TypeScript parity

- [ ] engine contracts
- [ ] `EnginePolicy`
- [ ] utility engine
- [ ] MDP engine
- [ ] simulator and bench

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
| Engine contract | planned |
| Utility engine | planned |
| MDP planner | planned |
| Calibration | planned |
| Model learning | planned |
| POMDP | planned |
