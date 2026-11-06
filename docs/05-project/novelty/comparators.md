# Comparators

Documented capability comparison for the prior-art matrix in
[prior-art.md](prior-art.md). Every row is based on public documentation and
source code at the version and date noted. No adapter has been run yet; this
is a capability comparison, not a performance comparison.

## Search log

| Date | Source | Query | Hits kept |
|---|---|---|---|
| 2026-11-06 | docs.langchain.com/langgraph | "human in the loop" "interrupt" "checkpoint" | LangGraph |
| 2026-11-06 | docs.temporal.io | "approval" "compensation" "audit" "workflow history" | Temporal |
| 2026-11-06 | support.pagerduty.com | "escalation policy" "on-call schedule" "audit log" | PagerDuty |
| 2026-11-06 | microsoft.github.io/autogen | "human input" "decision" | AutoGen |
| 2026-11-06 | docs.crewai.com | "human input" "task output" | CrewAI |
| 2026-11-06 | camunda.com/docs | "approval" "compensation" "decision" "audit" | Camunda |
| 2026-11-06 | docs.opsgenie.com | "escalation" "routing" "schedule" | Opsgenie |
| 2026-11-06 | github topics | ai-agents decision-engine durable-execution policy-engine | — |
| 2026-11-06 | research.microsoft.com + arXiv | "commitment-based multi-agent" "social commitments" | FIPA / BDI |
| 2026-11-06 | scipy calibration docs | "reliability diagram" "calibration curve" "brier score" | scikit-learn |

## Capability matrix

| Capability | LangGraph | Temporal | PagerDuty | AutoGen | Camunda | LAIX |
|---|---|---|---|---|---|---|
| One decision contract (verb + reason + score + audit in one object) | no | no | no | no | no | **yes** |
| Commitments in the decision | no | no | no | no | no | **yes** |
| Execution risk in the decision (reversible, approval, recovery) | partial | partial | no | no | partial | **yes** |
| Human attention budget | partial | no | partial | partial | no | **yes** |
| Timing and revision semantics (cooldown, hysteresis, deadline) | partial | partial | no | no | no | **yes** |
| Calibration from outcomes (ECE, Brier, decision accuracy) | no | no | partial | no | no | **yes** |
| Auditable decision trail (reason code, score breakdown, trace id) | partial | yes | yes | no | yes | **yes** |
| Host-owned execution | yes | no | no | yes | no | **yes** |
| Training-free default | yes | yes | yes | yes | yes | **yes** |
| Python/TypeScript parity | yes | yes | n/a | yes | n/a | **yes** |

**Partial** means the system covers the concern in some form but not in a
decision contract field that travels with the decision object.

## Per-system paragraphs

### LangGraph (v0.2, LangChain Inc., 2024–2026)

LangGraph is a stateful graph framework for multi-agent and human-in-the-loop
workflows. It supports interrupts for human approval, checkpointed thread state
and conditional edges. These cover execution safety (a node can wait for human
input) and partial audit (the thread history is reproducible). What LangGraph
does not have: a unified decision object that carries the verb, reason code,
commitment state, execution risk, score breakdown and audit trail in one
structure. Each node returns an arbitrary value; the host is responsible for
recording why a decision was made. There is no commitment model, no attention
budget and no calibration from outcomes. LangGraph is closest to LAIX in the
human-in-the-loop category.
Source: https://langchain-ai.github.io/langgraph/

### Temporal (v1.x, Temporal Technologies, 2020–2026)

Temporal is a durable execution platform for workflows and activities. It
provides retries, timeouts, timers, signals and full workflow history replay.
Compensation (saga-like) is supported through compensating activities. The
workflow history constitutes an auditable trail. What Temporal does not have:
a decision object. Temporal executes a workflow; it does not decide which verb
to take, nor does it carry a reason code, commitment state, execution risk
estimate or attention budget in a decision structure. The host writes the
decision logic; Temporal ensures durability. Approval requires a signal from
the host. Temporal is closest to LAIX in the execution integrity and audit
categories.
Source: https://docs.temporal.io/

### PagerDuty (v3.x, PagerDuty Inc., 2020–2026)

PagerDuty is an incident alerting and on-call management platform. It routes
alerts to on-call engineers via escalation policies, schedules and suppression
rules. It records a full incident log and provides analytics on MTTD and MTTR.
What PagerDuty does not have: a decision contract. Alert routing is a rules
engine, not a verb-with-reason-code decision. There is no commitment model,
no execution risk estimate, no attention budget as an explicit field (on-call
schedules are an implicit attention proxy), and no calibration from alert
outcomes in the decision sense. PagerDuty is closest to LAIX in the escalation
and audit categories.
Source: https://support.pagerduty.com/

### AutoGen (v0.4, Microsoft Research, 2023–2026)

AutoGen is a multi-agent conversation framework with human proxy agents for
human-in-the-loop. The human proxy can interrupt a conversation; the
orchestrator routes messages between agents. What AutoGen does not have: a
decision contract. Each agent message is free-form; there is no verb,
reason code, commitment state, execution risk or score. Human input is a
conversation turn, not a structured decision. AutoGen is closest to LAIX in
the multi-agent coordination and human-in-the-loop categories.
Source: https://microsoft.github.io/autogen/

### Camunda (v8.x, Camunda GmbH, 2020–2026)

Camunda is a BPMN process orchestration platform. It supports human tasks for
approval workflows, compensation events for saga-like rollback and a full
process audit log. The DMN (Decision Model and Notation) component provides
rule-based decisions. What Camunda does not have: a unified live-decision
contract. DMN decisions return a table result; they do not carry a reason code,
commitment state, attention budget or calibration. Approval is modelled as a
user task, not as a flag on a decision object. Camunda is closest to LAIX in
the approval, compensation and audit categories.
Source: https://docs.camunda.io/

### FIPA ACL / BDI commitment-based multi-agent systems (academic)

The FIPA ACL specification and subsequent commitment-based multi-agent research
(Winikoff 2007, Singh 2008, Chopra & Singh 2015) formalise social commitments
as first-class objects in multi-agent communication. A commitment carries
debtor, creditor, antecedent and consequent; it can be created, cancelled,
released, delegated and discharged. This is the closest academic work to
LAIX's commitment model. What this line does not cover: execution risk,
attention budget, calibration and an auditable decision trail in a single
contract. It models commitment state but not the full decision around it.
Source: FIPA FIPA00061 ACL Message Structure Specification;
Chopra, A. K. & Singh, M. P. (2015). Custard: Computing norm compliance of
sociotechnical systems, AAMAS 2015.

### scikit-learn calibration (1.4.x, scikit-learn team)

scikit-learn provides reliability diagrams, `CalibratedClassifierCV`,
`calibration_curve`, Brier score and expected calibration error. This is the
standard reference implementation for classifier calibration. What
scikit-learn does not have: decision calibration (calibration from decision
outcomes, not class probabilities) or integration with a decision contract.
LAIX's `CalibrationReport` and `DecisionCalibrationReport` apply the same ECE
and Brier concepts to live decisions and to per-verb accuracy, which is not
covered by scikit-learn calibration.
Source: https://scikit-learn.org/stable/modules/calibration.html

## Closest prior work statement

The closest system in agent orchestration is **LangGraph**, which provides
checkpoints, interrupts and human approval but returns arbitrary node values
rather than a structured decision. The closest system in durable execution is
**Temporal**, which provides full workflow history and compensation but does
not expose a verb-with-reason-code decision object. The closest system in
alerting is **PagerDuty**, which routes and escalates alerts with an audit log
but has no commitment model or execution risk estimate. The closest academic
line is **FIPA ACL / social commitments**, which formalises promise state but
not execution risk, attention budget or calibration. No compared system combines all ten
capabilities in one contract. LAIX integrates commitment state, execution risk, human
attention budget, decision timing, calibration and auditable revision in a single
training-free decision object.

## Claims that remain defensible after the comparison

1. No compared system carries verb + reason code + commitment state +
   execution risk + attention budget + score breakdown in one decision object.
2. Host-owned execution is a differentiator: LangGraph is host-owned; Temporal
   and PagerDuty are not.
3. Training-free default is not a differentiator: all compared systems have
   rule-based or deterministic defaults.
4. Calibration from decision outcomes (not class probabilities) is not covered
   by any compared system.
5. The integration of all ten capabilities in one contract is the novelty; each
   individual capability has prior art.

## Measured operational comparison (LangGraph)

The LangGraph adapter is runnable when `langgraph` is installed. It puts the same
`LiveDecisionEngine` inside a state graph with a decision node and an approval interrupt. That
isolates orchestration overhead; it is not an accuracy comparison.

| Metric | Result |
|---|---:|
| Cases | 120 |
| Decisions | 120 |
| Approval interrupts | 0 |
| Mean latency | 6-7 ms |
| Adapter glue code | 110 lines |
| Dependencies | `langgraph` |
| Result file | `results/live-bench/harness-v2/reports/external-comparison.json` |

Reproduce with:

```bash
python -m pip install -r benchmarks/compare/requirements-external.txt
python scripts/novelty/compare/run_external_comparison.py --split all
```

Temporal, PagerDuty and Camunda remain documented-only because they need a server or account.


## What remains unmeasured

- LangGraph decision accuracy against LAIX is not meaningful: the adapter runs the same LAIX engine
  inside the graph. The measured result is orchestration overhead, not planner quality.
- Temporal requires a Temporal server and a worker for latency, retries and signal measurements.
- PagerDuty and Camunda require accounts or servers.
- Glue code for Temporal/Camunda remains a documented estimate until those systems run.

These are Level 2 (external system comparison) tasks; see
[prior-art.md](prior-art.md) for the protocol.
