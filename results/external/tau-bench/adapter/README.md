# τ-bench LAIX guardrail adapter

This adapter gates mutating retail tool calls through `LiveDecisionEngine` and asks the user to
confirm before execution. It is a **generic approval guardrail**, not a full retail policy engine.

## Install into a τ-bench clone

```bash
git clone https://github.com/sierra-research/tau-bench.git
cd tau-bench
pip install litellm termcolor pydantic numpy mcp
cp /path/to/laix/results/external/tau-bench/adapter/lai_x_agent.py tau_bench/agents/
```

Add `"laix"` to the strategy choices in `run.py`:

```python
choices=["tool-calling", "act", "react", "few-shot", "laix"],
```

Add `"laix"` to the assertion in `tau_bench/run.py`:

```python
assert config.agent_strategy in ["tool-calling", "act", "react", "few-shot", "laix"]
```

Add the branch in `agent_factory` before the `"act"` branch:

```python
elif config.agent_strategy == "laix":
    from tau_bench.agents.lai_x_agent import LAIXGuardrailAgent

    return LAIXGuardrailAgent(
        tools_info=tools_info,
        wiki=wiki,
        model=config.model,
        provider=config.model_provider,
        temperature=config.temperature,
    )
```

## Run

```bash
export LAIX_SRC=/path/to/laix/packages/python/laix/src
export OPENAI_API_KEY=...
export OPENAI_API_BASE=https://api.deepseek.com
export PYTHONIOENCODING=utf-8

python run.py --agent-strategy laix --env retail \
  --model deepseek-v4-flash --model-provider openai \
  --user-model deepseek-v4-flash --user-model-provider openai \
  --user-strategy llm --max-concurrency 2 \
  --task-ids 0 1 2 3 4 5 6 7 8 9 --num-trials 1 --log-dir results-laix
```

## Scope

The guard:

- passes read-only tools through;
- for mutating tools, asks `LiveDecisionEngine` whether to act or ask;
- if the user has confirmed in the latest user message, executes;
- otherwise returns an "Approval required" tool result and lets the model ask the user.

It does not encode the retail policy rules (authentication, pending-order restrictions, payment
method rules). Those need a domain adapter before τ-bench can test the full runtime claim.
