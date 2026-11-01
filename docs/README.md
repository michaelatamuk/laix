# LAIX documentation

One page per concept. Start with the architecture, then pick the guide you need.

## Start here

| Page | What it answers |
|---|---|
| [architecture.md](architecture.md) | What is LAIX, what are the verbs, and how do the parts fit? |
| [structure.md](structure.md) | Where does each package and module live? |
| [decisions.md](decisions.md) | What does one decision contain? |
| [contracts.md](contracts.md) | What is the versioned data contract? |

## Guides

| Page | What it covers |
|---|---|
| [integration.md](integration.md) | Install LAIX, build an adapter, pin a version |
| [policy-packs.md](policy-packs.md) | The eight reference policies and the ten decision classes |
| [live-context.md](live-context.md) | Detectors, cheap/deep admission, perception frames |
| [outcome-learning.md](outcome-learning.md) | Measured outcomes, rewards and the UCB learner |
| [bench.md](bench.md) | LAIX-Bench suites, report and CLI |
| [platform.md](platform.md) | The south platform contract |
| [stores.md](stores.md) | State store and outcome store contracts |

## Evaluation

| Page | What it covers |
|---|---|
| [evaluation.md](evaluation.md) | Contract vectors, conformance and what to add next |

## Examples

Runnable examples live in [`../examples/README.md`](../examples/README.md). Every Python and
TypeScript capability has an example, and the test suite runs them.
