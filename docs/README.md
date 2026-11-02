# LAIX documentation

If you are new to LAIX, start with [What is LAIX?](what-is-laix.md) — plain
English, no code. Then read [Host integration](host-integration.md) for the six
things a product team checks first.

For the design: [architecture](architecture.md), then the core pages in numeric order,
starting with [the decision contract](core/01-decision-contract.md).

The split follows the code:

- **Core** — the decision layer.
- **App kit** — optional integration.
- **Boundaries** — PPMA, LAIX and other hosts.

## Understand LAIX

| Page | Answers |
|---|---|
| [what-is-laix.md](what-is-laix.md) | What is LAIX, in plain language? |
| [host-integration.md](host-integration.md) | Where does a host call it, and what does the host keep? |
| [architecture.md](architecture.md) | What is LAIX and how do the parts fit? |
| [structure.md](structure.md) | Where does each file live? |
| [boundaries.md](boundaries.md) | Where does PPMA end and LAIX begin, and what belongs to core, app kit and host? |
| [ppma-laix.md](ppma-laix.md) | Why use LAIX in PPMA? |
| [decision-models.md](decision-models.md) | How does LAIX relate to decision models? |

## Core (read in order)

| Page | Covers |
|---|---|
| [core/01-decision-contract.md](core/01-decision-contract.md) | the decision contract: request, response and records |
| [core/02-attention.md](core/02-attention.md) | task-level attention and its scope |
| [core/03-packaged-policies.md](core/03-packaged-policies.md) | the eight packaged policies |
| [core/04-outcome-learning.md](core/04-outcome-learning.md) | rewards, UCB and `BanditPolicy` |
| [core/05-evaluation.md](core/05-evaluation.md) | vectors, conformance and bench |
| [core/06-engine-roadmap.md](core/06-engine-roadmap.md) | the next planner and engine work |

## App kit

| Page | Covers |
|---|---|
| [appkit/integration.md](appkit/integration.md) | install, adapter, rollout and pinning |
| [appkit/live-context.md](appkit/live-context.md) | detectors, admission and frames |
| [appkit/platform.md](appkit/platform.md) | the platform contract |
| [appkit/stores.md](appkit/stores.md) | state and outcome stores |
| [appkit/bench.md](appkit/bench.md) | LAIX-Bench suites and CLI |

## Examples

Runnable examples live in [`../examples/README.md`](../examples/README.md). Every Python and
TypeScript capability has an example, and the test suite runs them.
