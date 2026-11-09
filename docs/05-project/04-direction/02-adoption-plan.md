# Adoption plan

This page is the working plan for taking LAIX from a repository with strong internal evidence to a
system that teams adopt. It is a plan, not a claim of traction.

The premise:

- A benchmark win is evidence, not adoption.
- A cloned integration is a compatibility demo, not value.
- Industry adopts what reduces risk, cost or audit effort, and what fits the stack a team already
  runs.

Adoption therefore needs four proofs: technical validity, relevance, economic value and
organizational fit.

| Proof | Question | Evidence |
|---|---|---|
| Technical | Does it work, and where does it fail? | External benchmarks, replication, negative results. |
| Relevance | Does it solve a job someone already pays for? | Design partners, interviews, incident data. |
| Economic | Is the benefit larger than integration and ownership cost? | Before/after pilot metrics. |
| Organizational | Can it pass security, procurement and audit? | Compliance crosswalk, audit pack, reference customer. |

## The first wedge

Start with **auditable, approval-aware decisions in operations and incident response**.

Why this wedge:

- The cost of a bad decision is visible.
- Actions are often irreversible and need approval.
- Incident response is a sequence, so continuity matters.
- Audit and post-incident review are already part of the process.
- The repository already has relevant evidence: the continuity benchmark, the live decision
  benchmark and the Sev1-Bench result, including its negative result.

Alternative wedges: support escalation, fintech operations, healthcare triage, procurement. Choose
one. Do not run several verticals in the first quarter.

## Workstreams

### 1. Benchmarks

Use benchmarks to falsify claims and to earn credibility, not as the adoption strategy.

Keep the internal benchmarks as regressions:

- live decision benchmark, 120 cases with a frozen 30-case test split;
- LAIX-Bench, 25 cases across 10 decision classes;
- continuity benchmark, 12 episodes and 60 decisions;
- planner simulation and stream bench.

Add external evidence:

- a full policy adapter for tau2-bench or tau3-bench, reporting `pass^1`, `pass^k`, policy violations,
  cost and latency;
- decision-specific scoring on Sev1-Bench: approval correctness, irreversible-action rate,
  continuity errors, audit completeness and recovery;
- a public specification for a decision-quality suite, with external annotators, a private holdout
  and adversarial cases.

Acceptance criteria for an external result:

- at least 100 cases per decision class;
- at least two external baselines;
- effect size, confidence interval and significance;
- pre-registration before the run;
- a reproducible artifact;
- negative results published;
- independent replication.

Do not chase saturated benchmarks. A benchmark win that the market does not trust is not adoption.

First step: build the tau2/tau3 adapter and the decision-specific Sev1 scoring, then publish a
"where LAIX helps and where it does not" report.

### 2. Design partners and pilots

Find teams with agents already in production and high-cost decisions.

Where to look:

- startup directories and portfolios focused on AI agents, operations and support automation;
- review categories for AI agents, AIOps, incident management and customer service AI;
- issue trackers and discussions for LangGraph, CrewAI, Temporal, n8n and incident tooling;
- practitioner communities for AI engineering, SRE and DevOps;
- conferences and local meetups.

A good partner:

- 50 to 500 people;
- agents in production or a serious pilot;
- frequent, expensive or irreversible decisions;
- approval, audit or regulatory pressure;
- willing to provide anonymized data and two or three people.

Pilot shape:

- four to six weeks;
- fixed fee, or free in exchange for a case study;
- baseline is the current process; treatment is the LAIX adapter;
- the same tasks and blind evaluation;
- metrics: decision quality, time to decision, escalation rate, rollback and incident rate, cost per
  decision, audit time, integration effort.

Outreach:

> Hi - we are building LAIX, a decision layer for agents that must ask for approval, keep promises
> and leave an audit trail. We are looking for three teams running agents in production with
> high-cost decisions. Would you be open to a 30-minute call? In exchange: a free four-week
> integration and a written decision-readiness report.

First step: build a list of 50 companies and send 10 messages per week.

Metric: three signed pilots, one with a measured before/after result.

### 3. Embedding and OEM

Do not fork other products. Ship adapters and plugins.

Target categories:

| Category | Targets |
|---|---|
| Agent frameworks | LangGraph, CrewAI, Microsoft Agent Framework, OpenAI Agents SDK, Google ADK, Pydantic AI, Mastra, Vercel AI SDK, AWS Strands |
| Durable execution | Temporal, DBOS, Inngest, Restate |
| Workflow and RPA | Camunda, n8n, Zapier, Make, UiPath, Automation Anywhere, ServiceNow, Appian, Pega |
| Observability | LangSmith, Langfuse, Arize Phoenix, Braintrust, Datadog, Dynatrace, Splunk, W&B Weave, Comet Opik |
| Incident and operations | PagerDuty, incident.io, FireHydrant, Rootly, Grafana OnCall, ServiceNow ITOM |
| Support | Zendesk, Intercom, Salesforce Service Cloud, Ada, Forethought |
| Cloud agent platforms | AWS Bedrock Agents, Azure AI Foundry Agent Service, Google Vertex AI, Salesforce Agentforce, Microsoft Copilot Studio |

Integration model:

- adapter or plugin, not a fork;
- a decision node inside a graph or workflow;
- OpenTelemetry and OCSF export;
- a marketplace listing;
- co-marketing and a joint case study.

First three adapters:

1. LangGraph: decision node, interrupt and checkpointer.
2. Temporal: activity or workflow, approval signal and retry.
3. PagerDuty or Datadog: incident context, decision, approval and action.

First step: make one production-grade adapter and publish a working "LAIX inside LangGraph" guide.

Metric: time to first decision under 30 minutes, integration under 100 lines, one partner case study.

### 4. Standards and interoperability

Publish the decision contract as a format other tools can read and write.

Artifacts:

- `laix-decision.v1.schema.json` for `Decision` and `DecisionRecord`;
- `laix-reason-codes.v1.json`, a stable registry;
- OpenTelemetry attributes such as `laix.decision.id`, `laix.verb`, `laix.reason_code`,
  `laix.policy.version`, `laix.confidence` and `laix.approval.required`;
- an OpenLineage facet for decision runs;
- a W3C PROV mapping;
- an MCP server that exposes `decide`;
- an A2A agent card;
- an OpenAPI profile for actions.

The decision schema, reason-code registry, MCP server, A2A card and OpenAPI profile are now in the
repository. The OpenLineage facet, W3C PROV mapping and OpenTelemetry collector remain.

Adoption path:

- publish the specification, a reference implementation and three emitters: Python, TypeScript and an
  OpenTelemetry collector;
- submit to the relevant OpenTelemetry, CNCF or Linux Foundation working groups;
- publish integration guides;
- do not require anyone to adopt the whole framework. It is enough that other tools read and write
  the format.

First step: one-page specification, a schema package and one external consumer.

Metric: an external project reads or writes `DecisionRecord` without help.

### 5. Compliance, audit and liability

This is likely the strongest non-benchmark path for LAIX.

Current dates to verify before using them in sales material:

- EU AI Act: most rules apply from 2 August 2026;
- high-risk systems under Annex III: 2 December 2027, after the Digital Omnibus;
- high-risk systems under Annex I: 2 August 2028;
- Article 50 transparency: 2 August 2026;
- EU Product Liability Directive (EU) 2024/2853: applies from 9 December 2026;
- DORA: in force since 17 January 2025;
- voluntary frameworks: NIST AI RMF, ISO/IEC 42001, SOC 2.

Product surface:

- `laix audit export` to JSON, CSV, OCSF or a SIEM;
- immutable records, retention and deterministic replay;
- a crosswalk: AI Act Article 12 logging to `DecisionRecord`; Article 14 human oversight to
  `requires_approval`, `ask` and `escalate`; Article 15 accuracy and robustness to tests,
  calibration and confidence; product liability to trace, policy version and decision id;
- approval and escalation evidence;
- an answer to "why did the agent do this?" in under an hour.

First step: write a ten-page audit pack, have a lawyer or compliance consultant review it, and
publish a redacted sample.

Metric: legal review passed; a customer can answer an audit question in under an hour.

### 6. Developer-first wedge

Build a free tool that solves a developer pain before asking for a runtime commitment.

Candidate scope:

- `laix explain <trace>`: read an OpenTelemetry, LangSmith or Langfuse trace and print the decision
  timeline, constraints, approvals and reason codes;
- `laix lint`: find loops, repeated actions, budget violations and missing approvals;
- `laix replay`: check determinism;
- `laix test`: turn an incident into a regression case.

Distribution:

- PyPI and npm;
- a GitHub Action;
- a VS Code extension;
- an OpenTelemetry collector;
- ready integrations with LangGraph, Temporal and n8n.

Model: open core. The developer tool is free; runtime, cloud and enterprise audit are paid.

First step: a two-week MVP on existing records, demonstrated on a real LangGraph trace.

Metric: 100 installs, 10 weekly active users and three issues from strangers.

### 7. Evaluation as a service

Do not compete with tracing platforms. Sell decision readiness.

Offer:

- a two-week audit over 50 to 100 scenarios;
- a scorecard: constraint satisfaction, approval correctness, irreversibility, continuity,
  calibration and audit completeness;
- a report, a regression suite and recommendations;
- price: EUR 10k to 25k, then a quarterly retainer.

Buyers:

- teams already running agents and worried about irreversible actions;
- regulated teams in fintech, health, insurance and energy;
- automation consultancies and system integrators.

First step: package the audit from LAIX-Bench plus a custom corpus, then run three outbound
conversations.

Metric: three audits and one retainer.

### 8. Open source, community and marketplaces

Channels:

- GitHub Discussions and Discord;
- monthly office hours;
- good-first-issues and integration bounties;
- hackathons;
- conferences: AI Engineer, SREcon, KubeCon and local AI meetups;
- marketplaces: AWS, Azure, Google Cloud, GitHub, Datadog, ServiceNow, UiPath and Vercel.

Content:

- a weekly decision teardown of a real incident;
- monthly release notes;
- benchmark updates, including negative results;
- "how to integrate LAIX with X" guides.

Metrics:

- activated integrations, not stars;
- time to first decision;
- external contributors;
- issue response time;
- retention.

First step: contribution guide, ten good-first-issues, a Discord and one teardown.

### 9. Academia

Venues:

- NeurIPS Datasets and Benchmarks, Agents;
- ICML, ICLR, AAAI, IJCAI;
- AAMAS and UAI;
- CHI and CSCW for human oversight;
- FAccT and EAAMO for accountability;
- ACL and EMNLP for agents;
- JAIR, Management Science, Operations Research and Decision Analysis.

Model:

- co-author with a lab;
- publish an artifact and pre-registration;
- invite independent replication;
- run a workshop on decision runtimes and evaluation;
- apply for grants: NSF SBIR/STTR, EU EIC, Horizon Europe.

First step: a four-page workshop paper and an artifact, submitted to NeurIPS Datasets and Benchmarks
or AAMAS; invite two labs to replicate.

Metric: one independent replication, one workshop and one joint grant.

### 10. Services, consulting and training

Offer:

- a two-week decision audit;
- a four-to-six-week integration sprint;
- team training;
- architecture review.

Prices:

- audit: EUR 10k to 25k;
- sprint: EUR 30k to 80k;
- optional success fee.

Buyers:

- AI platform teams;
- automation consultancies;
- system integrators;
- cloud partners.

First step: a one-page offer and ten conversations with consultancies.

Metric: two paid engagements.

### 11. Vertical product

Wedge: incident response and SRE.

Product: an approval-aware incident copilot.

- collect incident context;
- propose an action with a reason code;
- require approval for irreversible actions;
- record an execution receipt;
- verify the result;
- preserve continuity across steps;
- export the audit trail.

Ideal customer profile: 50 to 500 engineers, on-call rotation, PagerDuty or Datadog, SLOs, expensive
or regulated incidents.

Metrics: MTTR, risky actions avoided, escalation rate, audit time and rollback rate.

First step: five interviews and one pilot.

### 12. Pain discovery

Search queries:

- `"human in the loop" agent approval`
- `"agent" "irreversible" OR "rollback"`
- `"why did the agent"`
- `"agent loop" cost`
- `"approval" LangGraph`
- `"audit" "AI agent"`
- `"escalation" agent production`

Sources:

- GitHub issues and discussions;
- the AI Incident Database and the OECD AI Incidents Monitor;
- postmortems and engineering blogs;
- review sites;
- practitioner communities;
- your own users' logs.

Interview script:

1. Which three bad agent decisions do you remember?
2. What happened, what did it cost and who noticed?
3. How did you detect it and what did you do?
4. What workaround did you build?
5. Who owns the budget?
6. What would have to be true for you to buy a solution?

Prioritize by: pain, frequency, cost of error, willingness to pay, integrability, sales cycle and
regulatory pull.

First step: 20 interviews in three weeks and a choice of two segments.

Metric: five painful problems with a budget attached.

## 90-day plan

| Period | Work |
|---|---|
| Days 1-14 | Choose the wedge; write the ideal customer profile; build the compliance crosswalk; fix the benchmark plan. |
| Days 15-45 | Sign three design partners; ship the LangGraph and PagerDuty adapters; build the `laix explain` MVP; run ten interviews. |
| Days 46-75 | Run the pilots; publish the "where it helps" report; submit a workshop paper; package the audit offer. |
| Days 76-90 | Publish one case study; set pricing; decide to scale or change the wedge. |

Gates:

- three signed pilots;
- one measured improvement;
- one external replication started;
- one paid audit;
- otherwise change the wedge, not the vision.

## What not to do

- Do not clone random repositories as proof of value. That is a compatibility demo.
- Do not chase saturated benchmarks.
- Do not sell a framework. Sell the outcome: less risk, lower MTTR, faster audit, fewer escalations.
- Do not compete with observability platforms on tracing. Integrate with them.
- Do not claim production readiness or a `1.0` without external validation.
- Do not mix product-led growth and enterprise sales in the same motion. The developer tool is
  bottom-up; compliance is top-down.
