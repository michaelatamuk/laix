# Core building blocks

LAIX core only. Read bottom-up: each row builds on the row below it.

```mermaid
block-beta
    columns 1

    block:capabilities["Capabilities"]
        columns 3
        decide["Decide<br/>by policy=... or request shape"]
        learn["Learn from outcomes<br/>outcome → reward → next choice"]
        evaluate["Evaluate<br/>cases · parity · bench"]
    end

    block:contract["Contract"]
        columns 3
        request["Decision request<br/>signals/context or situation/options"]
        response["Decision response<br/>verb · reason · confidence · action"]
        trail["Execution trail<br/>receipt · trace"]
    end

    block:engines["Engines"]
        columns 3
        attention["Attention<br/>signals · priority"]
        policies["Policies<br/>action · safety · replanning · allocation<br/>negotiation · preference · verification · escalation"]
        resources["Resources<br/>budget · admission"]
    end

    block:foundation["Foundation"]
        columns 3
        schema["Schema<br/>records · build · check"]
        sensing["Sensing<br/>detector · event · frame"]
        support["Support<br/>ids · time · values · errors · version"]
    end

    style capabilities font-size:22px,font-weight:bold
    style contract font-size:14px
```

## The rows

| Row block | Contains | What it is |
|---|---|---|
| **Capabilities** | Decide · Learn from outcomes · Evaluate | What the core can do. |
| **Contract** | Decision request · Decision response · Execution trail | The boundary and its records. |
| **Engines** | Attention · Policies · Resources | The engines and admission control. |
| **Foundation** | Schema · Sensing · Support | The shared records and foundations. |

## Request shapes

Without `policy=`, the request shape selects one of the two built-in engines:

| The call has | The engine |
|---|---|
| `signals` + `context` | Attention |
| `situation` + `options` | Action policy |
| `policy=...` | The policy you pass |

Packaged and custom policies are always selected explicitly.

## Learning loop

```text
outcome → reward → ledger → bandit → a better policy
outcome → label → feedback → better attention
```

## What each part contains

| Part | Contains | Built on |
|---|---|---|
| **Decide** | `policy=...` or request shape; return the response | Contract, engines, support |
| **Learn from outcomes** | outcome → reward → ledger → bandit → better policy; outcome → label → feedback → better attention | Support |
| **Evaluate** | cases, parity, report, bench | Contract, engines, support |
| **Decision request** | signals + context or situation + options | Support |
| **Decision response** | verb, reason, confidence, action, evidence, approval | Support |
| **Execution trail** | execution receipt, trace | Support |
| **Attention** | signals, priority, timing | Contract, support |
| **Policies** | action, safety, replanning, allocation, negotiation, preference, verification, escalation | Contract, learning, support |
| **Resources** | budget, sensing option, admission | Support |
| **Schema** | records, build, check | Contract, learning, support |
| **Sensing** | detector, detection, event, frame | Support |
| **Support** | ids, time, values, errors, version | — |

## Reading the stack

- **Decide** is the entry point. It takes `policy=...` or a request shape and returns a response.
- **Learn from outcomes** turns a measured result into a better next choice for Policies and Attention.
- **Evaluate** checks the engines; it is not on the request path.
- **Decision request** and **Decision response** are the boundary.
- The request shape routes: `signals + context` → Attention; `situation + options` → Action policy.
- A packaged or custom policy is selected explicitly with `policy=...`.
- **Decision response** carries the verb, reason, confidence, action and approval.
- **Execution trail** records what happened after the response.
- **Attention**, **Policies** and **Resources** are the engines.
- **Schema**, **Sensing** and **Support** are the shared foundations.
