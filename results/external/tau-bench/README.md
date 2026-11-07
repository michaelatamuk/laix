# τ-bench baseline

Status: baseline only. No LAIX variant has been run.

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

| Metric | Value |
|---|---:|
| Retail tasks | 10 |
| Passed | 9 |
| `pass^1` | **0.90** |
| Failed task | `0` |

Task 0 failed on product/item exchange reasoning. Task 0 also passed in a separate single run, so the
simulated-user path is not deterministic across runs. The full trajectories are in
`retail-deepseek-v4-flash.json`; the compact rows are in `summary.json`.

## Why there is no LAIX variant yet

τ-bench scores the agent's product and policy reasoning through the final database state. It does
not score approval state, commitments, decision continuity or audit. A generic LAIX guardrail would
add an approval or verification step, but the benchmark's reward would not measure that value, and a
turn that does not change the final state can add noise or reduce `pass^k`.

To test LAIX meaningfully, the adapter must be a **domain policy layer** that encodes the retail
rules (authentication, pending orders, payment methods, allowed item changes) and then asks LAIX to
approve or block the model's proposed tool call. That is a larger adapter than the Sev1-Bench
guardrail, and it is the next integration step.

## Reproduce

```bash
git clone https://github.com/sierra-research/tau-bench.git
cd tau-bench
pip install litellm termcolor pydantic numpy mcp
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://api.deepseek.com
export PYTHONIOENCODING=utf-8

python run.py --agent-strategy tool-calling --env retail \
  --model deepseek-v4-flash --model-provider openai \
  --user-model deepseek-v4-flash --user-model-provider openai \
  --user-strategy llm --max-concurrency 2 \
  --task-ids 0 1 2 3 4 5 6 7 8 9 --num-trials 1 --log-dir results-baseline
```

## Limitations

- 10 of the retail tasks, one trial; not the full τ-bench suite.
- No airline domain.
- User-simulator nondeterminism: task 0 passed in a separate run and failed here.
- Baseline only; the LAIX policy adapter is not implemented.
- `deepseek-v4-flash` is served through the OpenAI-compatible endpoint, not a τ-bench-native
  provider.
