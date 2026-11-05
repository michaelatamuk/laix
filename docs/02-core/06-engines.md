# Decision engines

The engine contract, the built-in engines and the simulator are implemented in
`core/engines/`. The layer stays usable without any engine: rule policies and the
packaged policies still return the same decision shape.

The goal is:

- one engine contract;
- LAIX’s own engines;
- adapters for external engines;
- every engine returns the same `Plan`; the adapter returns the same `Decision` and uses the same
  lifecycle.

Build order and current status live in [the project roadmap](../05-project/roadmap.md).

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
| 1 | Problem shape | `DecisionProblem`, request projection |
| 2 | Option model | `ActionOption`, costs, risks and hard limits |
| 3 | Utility model | `UtilityModel`, weights, risk attitude |
| 4 | Planning | `DecisionEngine.solve`, `MDPEngine`, `POMDPEngine` |
| 5 | Calibration | `CalibrationReport` and confidence adjustment |
| 6 | Learning | `ModelLearner` for transitions and rewards |
| 7 | Explanation | chosen plan, alternatives, expected value |
| 8 | Simulator and bench | `Simulator`, engine comparison, optimality gap |

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

## Limits

- A planner needs a world model. The app supplies the domain transitions; LAIX plans over them.
- Utility elicitation remains the hard part.
- POMDPs get expensive quickly.
- Calibration needs real outcomes.
- Planner explanations are harder than rule traces.
- The API grows. Keep every piece optional.

See [the project roadmap](../05-project/roadmap.md) for status and next work.
