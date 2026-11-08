# τ-bench

Status: baseline and LAIX guardrail on a 10-task retail slice. Not the full suite.

[τ-bench](https://github.com/sierra-research/tau-bench) evaluates a full tool-using agent against a
simulated user and a domain policy in retail and airline tasks. The score is `pass^1` on one trial;
`pass^k` measures consistency over repeated trials.

## Setup

- Agent: DeepSeek V4 Flash, tool-calling, temperature 0.
- User simulator: DeepSeek V4 Flash, LLM strategy.
- Domain: retail.
- Tasks: 0–9 (10 tasks), one trial.
- OpenAI-compatible endpoint: `https://api.deepseek.com`.

The environment was run from a clone of τ-bench. The editable install fails on Windows because
`setup.py` reads `README.md` with the cp1252 codec; installing the dependencies directly and running
from the repository root works.

## Result

| Variant | Passed | `pass^1` |
|---|---:|---:|
| Tool-calling baseline | 9/10 | 0.90 |
| LAIX approval guardrail | **10/10** | **1.00** |

The guardrail asks the user to confirm a mutating tool call before it is executed. Task 0 is the
difference: the baseline followed a later user drift ("only the keyboard") and failed the benchmark's
expected two-item exchange; with the guardrail, the confirmation step produced a user confirmation
of both exchanges, and the final state matched the expected action.

This is a single trial on 10 tasks. It is a positive signal, not a significance claim.

## What the guardrail tests

The adapter in [`adapter/`](adapter/) passes read-only tools through and sends mutating tools through
`LiveCompositePlanner`:

- act when the user has confirmed;
- otherwise ask for confirmation;
- keep the model's message history and tool schema unchanged.

It is a **generic approval gate**. It does not encode the retail policy rules
(authentication, pending-order restrictions, payment-method rules, allowed item changes).

## What remains

To test the full runtime claim on τ-bench, the adapter must encode the retail policy and let LAIX
approve, block or escalate the model's proposed tool call. That is the next integration. Until then,
this result supports the guardrail position only.

## Reproduce

```bash
git clone https://github.com/sierra-research/tau-bench.git
cd tau-bench
pip install litellm termcolor pydantic numpy mcp
cp /path/to/laix/results/external/tau-bench/adapter/lai_x_agent.py tau_bench/agents/
# add the "laix" strategy to run.py and tau_bench/run.py as described in adapter/README.md

export LAIX_SRC=/path/to/laix/packages/python/laix/src
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://api.deepseek.com
export PYTHONIOENCODING=utf-8
```

Baseline:

```bash
python run.py --agent-strategy tool-calling --env retail \
  --model deepseek-v4-flash --model-provider openai \
  --user-model deepseek-v4-flash --user-model-provider openai \
  --user-strategy llm --max-concurrency 2 \
  --task-ids 0 1 2 3 4 5 6 7 8 9 --num-trials 1 --log-dir results-baseline
```

LAIX guardrail:

```bash
python run.py --agent-strategy laix --env retail \
  --model deepseek-v4-flash --model-provider openai \
  --user-model deepseek-v4-flash --user-model-provider openai \
  --user-strategy llm --max-concurrency 2 \
  --task-ids 0 1 2 3 4 5 6 7 8 9 --num-trials 1 --log-dir results-laix
```

## Files

- `retail-deepseek-v4-flash.json` — baseline trajectories.
- `summary.json` — baseline task/reward rows.
- `laix-guardrail-deepseek-v4-flash.json` — guardrail trajectories.
- `summary-laix.json` — guardrail task/reward rows.
- `adapter/` — the LAIX guardrail agent and installation notes.

## Limitations

- 10 retail tasks, one trial; not the full τ-bench suite.
- No airline domain and no `pass^k` estimate.
- Task 0 is a task-validity/user-drift case; the upstream repository warns that these tasks are
  outdated and points to τ²-bench.
- The guardrail is a generic approval gate, not a retail policy engine.
- `deepseek-v4-flash` is served through the OpenAI-compatible endpoint, not a native τ-bench
  provider.
