# Core map

Read this first. Every box is a package under `laix.core`. Arrows point from a package to what it
depends on, so the bottom is the foundation and the top is the entry point.

```mermaid
flowchart BT
    subgraph foundation["0 · Foundation"]
        support["support<br/>ids · time · values · verbs<br/>errors · serialize · version"]
    end

    subgraph contracts["1 · Contracts and records"]
        decisions["decisions<br/>request · response · trail · normalise"]
        outcome["outcome_learning<br/>Outcome · ledger · rewards<br/>UCB bandit · attention feedback"]
        sensing["sensing<br/>Detector · Detection · Event · Frame"]
    end

    subgraph engine_layer["2 · Engines"]
        engines["engines<br/>attention · policies · resources"]
    end

    subgraph proof["3 · Proof and schema"]
        evaluation["evaluation<br/>Case · compare · Report<br/>Row · attention replay"]
        schema["schema<br/>records · build · check"]
    end

    subgraph entry["4 · Entry"]
        dispatch["dispatch<br/>select · decide"]
    end

    support --> decisions
    support --> outcome
    support --> sensing

    decisions --> engines
    outcome --> engines
    support --> engines

    decisions --> evaluation
    engines --> evaluation
    support --> evaluation

    decisions --> schema
    outcome --> schema
    support --> schema

    decisions --> dispatch
    engines --> dispatch
    support --> dispatch

    classDef foundationStyle fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20;
    classDef contractsStyle fill:#e3f2fd,stroke:#1565c0,color:#0d47a1;
    classDef engineStyle fill:#fff3e0,stroke:#ef6c00,color:#e65100;
    classDef proofStyle fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c;
    classDef entryStyle fill:#fce4ec,stroke:#ad1457,color:#880e4f;

    class support foundationStyle;
    class decisions,outcome,sensing contractsStyle;
    class engines engineStyle;
    class evaluation,schema proofStyle;
    class dispatch entryStyle;
```

`laix.core` and `laix` are the public surface. They re-export names from these packages; they are not
an extra dependency layer.

## What each layer does

| Layer | Packages | Depends on |
|---|---|---|
| **0 · Foundation** | `support` | — |
| **1 · Contracts and records** | `decisions` | `support` |
| | `outcome_learning` | `support` |
| | `sensing` | `support` |
| **2 · Engines** | `engines` | `support`, `decisions`, `outcome_learning` |
| **3 · Proof and schema** | `evaluation` | `support`, `decisions`, `engines` |
| | `schema` | `support`, `decisions`, `outcome_learning` |
| **4 · Entry** | `dispatch` | `support`, `decisions`, `engines` |

## How to read it

- `support` is the base. It has no dependency inside `laix.core`.
- `decisions`, `outcome_learning` and `sensing` depend only on `support`.
- `engines` adds `decisions` and `outcome_learning`.
- `evaluation` compares decisions and engines; it sits above both.
- `schema` reads the record classes from `decisions` and `outcome_learning`.
- `dispatch` is the core entry point. It selects a policy or engine and returns decisions.
- The public surface re-exports these packages. It does not add behaviour.
