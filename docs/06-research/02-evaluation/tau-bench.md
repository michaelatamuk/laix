# τ-bench

Status: baseline run only. No LAIX variant has been run.

[τ-bench](https://github.com/sierra-research/tau-bench) evaluates a full tool-using agent against a
simulated user and a domain policy. It is the closest public benchmark to policy adherence and
multi-turn reliability, but it scores the whole agent, not a decision runtime.

## Baseline

- Agent and user simulator: DeepSeek V4 Flash.
- Domain: retail.
- Tasks: 0–9, one trial.
- Result: **9/10 passed**, `pass^1 = 0.90`.
- Failed task: 0. The model followed the user's latest instruction ("exchange only the
  keyboard") after the user changed their mind mid-conversation; the benchmark's expected action
  still assumed the original two-item exchange. This is a task-validity/user-drift issue, not an
  approval or policy violation.

The full trajectories are in
[`results/external/tau-bench/`](../../../results/external/tau-bench/README.md).

## The integration boundary

τ-bench rewards the final database state and policy-compliant actions. It does not score approval
state, commitments, continuity or audit. A generic LAIX guardrail — ask before a mutating tool call —
would add a turn but not necessarily change the final state or the reward.

To test LAIX meaningfully, the adapter must encode the retail policy:

- authenticate the user before account actions;
- block changes to pending orders;
- restrict payment-method changes;
- allow only item changes that match the catalogue;
- route a blocked call to ask, verify or escalate.

That is a **domain policy adapter** around the model's tool call. LAIX would be the decision
contract and guardrail; the model would still do the product and conversation reasoning.

## What would count as evidence

- Same 10 tasks, same model, same user simulator.
- Baseline: model decides and executes.
- LAIX: model proposes the tool call; LAIX checks it against the encoded policy and chooses act,
  ask, verify or escalate.
- Metrics: `pass^1`, `pass^k`, policy violations, unsafe actions, turns and cost.
- A result is only meaningful if the policy adapter is written before the run and both variants use
  the same tasks.

## Limitations

- 10 retail tasks, one trial; not the full suite.
- No airline domain.
- User-simulator nondeterminism: task 0 passed in a separate run and failed here. The failure was
  user-instruction drift, not a policy violation: the user changed the request to "only the
  keyboard" while the benchmark expected the original two-item exchange. The upstream τ-bench
  repository warns that these tasks are outdated; τ²-bench has fixed tasks.
- Baseline only; the policy adapter is not implemented.
- `deepseek-v4-flash` is served through the OpenAI-compatible endpoint, not a native τ-bench
  provider.
