# Concepts overview

The decision layer and app-kit pages describe the contracts. These pages explain the ideas behind them: what
LAIX is, where its boundary sits, how it relates to decision models and to PPMA, and how it is secured.

The whole system is one loop:

```text
request -> decision -> execution -> outcome -> next request
```

LAIX owns the decision and the decision trail. The host owns the product, the data, the execution and
the delivery.

## The three sections

| Section | Question | Pages |
|---|---|---|
| [Architecture](01-architecture/README.md) | What is LAIX, and where does it end? | [System architecture](01-architecture/01-system-architecture.md), [Scope and boundaries](01-architecture/02-scope-and-boundaries.md) |
| [Positioning](02-positioning/README.md) | How does LAIX relate to other ways of deciding? | [Decision models](02-positioning/01-decision-models.md), [PPMA integration](02-positioning/02-ppma-integration.md), [Robotics](02-positioning/03-robotics.md) |
| [Trust](03-trust/README.md) | What is the security and privacy boundary? | [Security](03-trust/01-security.md), [Privacy](03-trust/02-privacy.md) |

## Reading map

Read the sections in order. Each section opens with a short index that lists its pages in reading
order.

| Section | Covers |
|---|---|
| [Architecture](01-architecture/README.md) | The system, the decision, the verbs, the policy path and the boundary. |
| [Positioning](02-positioning/README.md) | Judgment models, decision layers and the PPMA split. |
| [Trust](03-trust/README.md) | Threat model, personal data, sharing and storage. |

The contracts live in [Decision overview](../02-decision/README.md). The optional app kit lives in
[App-kit overview](../03-appkit/README.md). The glossary and FAQ are in
[Reference](../05-reference/README.md).
