# τ-bench

Status: baseline and LAIX guardrail on a 10-task retail slice. Not the full suite.

[τ-bench](https://github.com/sierra-research/tau-bench) evaluates a full tool-using agent against a
simulated user and a domain policy. It is the closest public benchmark to policy adherence and
multi-turn reliability, but it scores the whole agent, not a decision runtime.

## Result

| Variant | Passed | `pass^1` |
|---|---:|---:|
| Tool-calling baseline | 9/10 | 0.90 |
| LAIX approval guardrail | **10/10** | **1.00** |

The guardrail asks the user to confirm a mutating tool call before execution. Task 0 is the
difference: the baseline followed a later user drift ("only the keyboard") and failed the benchmark's
expected two-item exchange; with the guardrail, the confirmation step produced a user confirmation
of both exchanges, and the final state matched the expected action.

This is a single trial on 10 tasks. It is a positive signal, not a significance claim.

## What the guardrail tests

The adapter in
[`results/external/tau-bench/adapter/`](../../../results/external/tau-bench/adapter/README.md) passes
read-only tools through and sends mutating tools through `LiveCompositePlanner`:

- act when the user has confirmed;
- otherwise ask for confirmation;
- keep the model's message history and tool schema unchanged.

It is a **generic approval gate**. It does not encode the retail policy rules
(authentication, pending-order restrictions, payment-method rules, allowed item changes).

## The integration boundary

τ-bench rewards the final database state and policy-compliant actions. It does not score approval
state, commitments, continuity or audit. The generic guardrail helped one user-drift case, but a
full runtime claim needs a domain policy adapter:

- authenticate the user before account actions;
- block changes to pending orders;
- restrict payment-method changes;
- allow only item changes that match the catalogue;
- route a blocked call to ask, verify or escalate.

That is the next integration. Until then, the τ-bench result supports the guardrail position only.

## What would count as stronger evidence

- More tasks and multiple trials, with `pass^k`.
- A domain policy adapter written before the run.
- Same model, same user simulator, same tasks for baseline and LAIX.
- Metrics: `pass^1`, `pass^k`, policy violations, unsafe actions, turns and cost.

## Limitations

- 10 retail tasks, one trial; not the full suite.
- No airline domain and no `pass^k` estimate.
- Task 0 is a task-validity/user-drift case; the upstream τ-bench repository warns that these tasks
  are outdated and points to τ²-bench.
- The guardrail is a generic approval gate, not a retail policy engine.
- `deepseek-v4-flash` is served through the OpenAI-compatible endpoint, not a native τ-bench
  provider.
