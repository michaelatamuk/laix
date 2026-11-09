# External benchmarks

Status: landscape reviewed; no external benchmark has been run.

No public benchmark measures a decision layer with commitments, attention, approvals, execution
risk and continuity. Several measure adjacent behaviour. LAIX must be evaluated as a component
inside a host agent, not as an end-to-end agent.

## Landscape

| Benchmark | What it measures | Fit | Status |
|---|---|---|---|
| [τ-bench](https://github.com/sierra-research/tau-bench) | Multi-turn tool-agent-user tasks, policy adherence and pass^k reliability in retail and airline | **best fit for policy adherence and consistency** | baseline 9/10; LAIX guardrail 10/10 on 10 tasks; full policy adapter pending |
| [ITBench](https://github.com/itbench-hub/ITBench) / [ITBench-AA](https://artificialanalysis.ai/evaluations/itbench-aa) | SRE incident diagnosis and remediation; ITBench-AA scores root-cause analysis | **best fit for incident response** | not run; public data and harness, heavy snapshots |
| [Sev1-Bench](https://github.com/edgedelta/sev1-bench) | 20 deterministic SRE incidents from public postmortems; diagnosis, remediation and forbidden actions | **best fit for a runnable incident replay** | [first component run](sev1-bench.md) |
| [JourneyBench](https://aclanthology.org/2026.eacl-industry.15.pdf) | Customer-support policy adherence and user-journey coverage | good fit for policy-driven support | not run; emerging |
| [DRIP-R](https://aclanthology.org/2026.findings-emnlp.522/) | Decision-making under ambiguous retail policy | good fit for ambiguity | not run; emerging |
| [Agentick](https://arxiv.org/abs/2605.06869) | General sequential decision-making across RL, LLM and VLM agents | weak fit; game-like, not enterprise | not run |
| [DecisionBench](https://arxiv.org/html/2605.19099v1) | Delegation between peer models in long-horizon workflows | not a fit; measures delegation | not run |
| [JevBench](https://github.com/Leanmcp/jevbench) | Typed decision-model accuracy, calibration and coherence | fit for the JEV chooser comparison, not the decision layer | not run; needs JEV API |

Broader enterprise suites such as WorkArena and TheAgentCompany measure task completion, not policy
adherence; they are less diagnostic for the decision layer. Agent safety suites such as AgentHarm,
AgentDojo and SafeAgentBench are adjacent: useful for execution risk, not for the full contract.

Several projects use the JevBench name. The row above refers to the typed-decision-model benchmark,
not the game benchmark.

First component run: Sev1-Bench, baseline 0.800 vs guardrail 0.800 (chooser 0.745, one forbidden
action). See [Sev1-Bench](sev1-bench.md).

## The right experiment

Do not compare LAIX to an LLM on a leaderboard. Compare two agents:

- **Baseline:** the same model, tools and policy prompt; the model decides.
- **LAIX:** the same model and tools; LAIX supplies the decision contract.

This isolates the decision layer. Report task success, policy violations, unsafe actions, pass^k,
turns, latency and cost.

## Metrics

### τ-bench

- pass^1 and pass^k;
- policy violation rate;
- task success;
- turns and cost.

### ITBench / ITBench-AA

- incident resolution rate;
- root-cause accuracy;
- unsafe or irreversible actions;
- steps and time to resolution.

### LAIX-specific

No world benchmark covers these; run the episode benchmark:

- promise keeping;
- attention budget adherence;
- approval correctness;
- revision correctness;
- continuity errors.

## First run

1. Choose τ-bench first: smaller, public, policy-focused and closest to the decision contract.
2. Build a thin host adapter: the model proposes, LAIX decides, the host executes.
3. Run baseline and LAIX on the same tasks, same model and same tools.
4. Report pass^k, policy violations, task success, cost and latency.
5. Repeat on ITBench for the incident-response case.

## Blockers

- LLM API access and budget for the agent and user simulator;
- a host adapter for τ-bench;
- ITBench public snapshots (large) and environment setup;
- JEV API access for the chooser comparison.

No result is claimed until these runs exist.
