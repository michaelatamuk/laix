# LAIX documentation

One page per concept. New to LAIX? Read [architecture](design/architecture.md), then
[reading a decision](design/decisions.md), then [contracts](design/contracts.md). The guides are
independent after that.

## Design

| Page | What it answers |
|---|---|
| [architecture.md](design/architecture.md) | What is LAIX, what are the verbs, and how do the parts fit? |
| [structure.md](design/structure.md) | Where does each package and module live? |
| [decisions.md](design/decisions.md) | What does one decision contain? |
| [contracts.md](design/contracts.md) | What is the versioned data contract? |

## Guides

| Page | What it covers |
|---|---|
| [integration.md](guides/integration.md) | Install LAIX, build an adapter, pin a version |
| [policy-packs.md](guides/policy-packs.md) | The eight reference policies and the ten decision classes |
| [live-context.md](guides/live-context.md) | Detectors, cheap/deep admission, perception frames |
| [outcome-learning.md](guides/outcome-learning.md) | Measured outcomes, rewards and the UCB learner |
| [bench.md](guides/bench.md) | LAIX-Bench suites, report and CLI |
| [platform.md](guides/platform.md) | The south platform contract |
| [stores.md](guides/stores.md) | State store and outcome store contracts |

## Evaluation

| Page | What it covers |
|---|---|
| [evaluation.md](evaluation.md) | Contract vectors, conformance and what to add next |

## Examples

Runnable examples live in [`../examples/README.md`](../examples/README.md). Every Python and
TypeScript capability has an example, and the test suite runs them.
