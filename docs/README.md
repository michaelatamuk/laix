# LAIX documentation

If you are new to LAIX, start with [What is LAIX?](what-is-laix.md) — plain
English, no code. Then read [Host integration](host-integration.md) for the six
things a product team checks first.

For the design: [architecture](architecture.md), then
[reading a decision](core/decisions.md), then [contracts](core/contracts.md).

The split follows the code:

- **Core** — the decision layer.
- **App kit** — optional integration.
- **Boundaries** — which layer owns what.

## Understand LAIX

| Page | Answers |
|---|---|
| [what-is-laix.md](what-is-laix.md) | What is LAIX, in plain language? |
| [host-integration.md](host-integration.md) | Where does a host call it, and what does the host keep? |
| [architecture.md](architecture.md) | What is LAIX and how do the parts fit? |
| [structure.md](structure.md) | Where does each file live? |
| [boundaries.md](boundaries.md) | What belongs to core, the app kit and the host? |
| [positioning.md](positioning.md) | How does LAIX relate to decision models? |

## Core

| Page | Covers |
|---|---|
| [core/contracts.md](core/contracts.md) | record shapes and the `0.8.0` version |
| [core/decisions.md](core/decisions.md) | verbs, fields and examples |
| [core/attention.md](core/attention.md) | task-level attention and its scope |
| [core/policy-packs.md](core/policy-packs.md) | the eight packaged policies |
| [core/outcome-learning.md](core/outcome-learning.md) | rewards, UCB and `BanditPolicy` |
| [core/evaluation.md](core/evaluation.md) | vectors, conformance and bench |
| [core/engine-roadmap.md](core/engine-roadmap.md) | the next decision-engine work |

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
