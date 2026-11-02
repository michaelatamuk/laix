# Core building blocks

LAIX core only. Read bottom-up: each row builds on the row below it.

```mermaid
block-beta
    columns 1

    capabilities["Capabilities<br/>Decide · Learn from outcomes · Evaluate"]
    contract["Contract<br/>Decision request · Decision response · Execution trail"]
    engines["Engines<br/>Attention · Policies · Resources"]
    foundation["Foundation<br/>Schema · Sensing · Support"]
```

## The rows

| Row block | Contains | What it is |
|---|---|---|
| **Capabilities** | Decide · Learn from outcomes · Evaluate | What the core can do. |
| **Contract** | Decision request · Decision response · Execution trail | The boundary and its records. |
| **Engines** | Attention · Policies · Resources | What produces a decision. |
| **Foundation** | Schema · Sensing · Support | The shared records and foundations. |

## What each part contains

| Part | Contains | Built on |
|---|---|---|
| **Decide** | `select` and `decide` | Contract, engines |
| **Learn from outcomes** | outcome, reward, ledger, bandit | Support |
| **Evaluate** | cases, parity, report, bench | Contract, engines |
| **Decision request** | signals, context, situation, options | Support |
| **Decision response** | verb, reason, confidence, action, evidence | Support |
| **Execution trail** | execution receipt, trace | Support |
| **Attention** | gates, score, timing | Contract, support |
| **Policies** | action and packaged policies | Contract, learning, support |
| **Resources** | budget, sensing option, admission | Support |
| **Schema** | records, build, check | Contract, learning, support |
| **Sensing** | detector, detection, event, frame | Support |
| **Support** | ids, time, values, verbs, errors | — |

## Reading the stack

- **Decide** is the entry point. It chooses a policy or engine and returns a response.
- **Learn from outcomes** turns a measured result into a better next choice.
- **Evaluate** checks the engines; it is not on the request path.
- **Decision request** and **Decision response** are the boundary: one request in, one response out.
- **Execution trail** records what happened after the response.
- **Attention**, **Policies** and **Resources** are the engines.
- **Schema**, **Sensing** and **Support** are the shared foundations.
