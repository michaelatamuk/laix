# Core building blocks

LAIX core only. Read bottom-up: each row builds on the row below it.

```mermaid
block-beta
    columns 1

    block:capabilities["Capabilities"]
        columns 4
        decide["Decide<br/>select · decide"]
        learn["Learn from outcomes<br/>outcome · reward"]
        evaluate["Evaluate<br/>cases · parity · bench"]
        explain["Explain<br/>reason · evidence · basis"]
    end

    block:contract["Contract"]
        columns 4
        request["Decision request<br/>signals · context · options"]
        response["Decision response<br/>confidence · action"]
        verb["Verb & reason<br/>verb · reason code"]
        trail["Execution trail<br/>receipt · trace"]
    end

    block:engines["Engines"]
        columns 4
        attention["Attention<br/>gates · score"]
        policies["Policies<br/>action · packaged"]
        registry["Registry<br/>name → policy"]
        resources["Resources<br/>budget · admission"]
    end

    block:foundation["Foundation"]
        columns 4
        schema["Schema<br/>records · build · check"]
        sensing["Sensing<br/>detector · event · frame"]
        support["Support<br/>ids · time · values · errors"]
        version["Version<br/>package · schema · rules"]
    end

    style capabilities font-size:22px,font-weight:bold
    style contract font-size:14px
```

## The rows

| Row block | Contains | What it is |
|---|---|---|
| **Capabilities** | Decide · Learn from outcomes · Evaluate · Explain | What the core can do. |
| **Contract** | Decision request · Decision response · Verb & reason · Execution trail | The boundary and its records. |
| **Engines** | Attention · Policies · Registry · Resources | What produces a decision. |
| **Foundation** | Schema · Sensing · Support · Version | The shared records and foundations. |

## What each part contains

| Part | Contains | Built on |
|---|---|---|
| **Decide** | `select` and `decide` | Contract, engines |
| **Learn from outcomes** | outcome, reward, ledger, bandit | Support |
| **Evaluate** | cases, parity, report, bench | Contract, engines |
| **Explain** | rationale, evidence, basis | Decision response |
| **Decision request** | signals, context, situation, options | Support |
| **Decision response** | confidence, action, approval | Support |
| **Verb & reason** | verb, reason code, rationale | Decision response |
| **Execution trail** | execution receipt, trace | Support |
| **Attention** | gates, score, timing | Contract, support |
| **Policies** | action and packaged policies | Contract, learning, support |
| **Registry** | policy name → policy object | Policies, support |
| **Resources** | budget, sensing option, admission | Support |
| **Schema** | records, build, check | Contract, learning, support |
| **Sensing** | detector, detection, event, frame | Support |
| **Support** | ids, time, values, errors | — |
| **Version** | package, schema and rule-set versions | Support |

## Reading the stack

- **Decide** is the entry point. It chooses a policy or engine and returns a response.
- **Learn from outcomes** turns a measured result into a better next choice.
- **Evaluate** checks the engines; it is not on the request path.
- **Explain** gives the reason, evidence and basis behind a response.
- **Decision request** and **Decision response** are the boundary.
- **Verb & reason** is the core of the response: what to do and why.
- **Execution trail** records what happened after the response.
- **Attention**, **Policies**, **Registry** and **Resources** are the engines.
- **Schema**, **Sensing**, **Support** and **Version** are the shared foundations.
