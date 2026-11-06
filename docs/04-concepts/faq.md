# FAQ

**What is LAIX?**

A decision layer for live AI experiences. It turns a request into one decision with a reason,
confidence and trail.

**Does LAIX use a model?**

The current layer is policy/rules based and training-free. Planners can use a world model the host
supplies: states, transitions and rewards. A pretrained model can sit behind `EnginePolicy`, and the
decision contract stays the same.

**Is LAIX an agent framework?**

LAIX is a layer inside one task. The host keeps orchestration, memory, execution, storage and
delivery.

**Where does execution happen?**

In the host. The optional app kit provides an execution bridge, receipts, recovery and records.

**What is the novelty?**

The integration: one training-free decision contract for commitments, execution risk, human
attention, calibration and decision time. `LiveDecisionEngine` combines the three live concerns in
one plan. The detailed evidence plan is in [Novelty and evidence](../05-project/novelty.md).

**When should I use it?**

When several tasks or products need consistent, timely, safe and auditable decisions, and you want
one contract instead of separate decision logic in each.

**Does LAIX train a model?**

The layer is training-free. Outcome learning, calibration and causal inference use the outcomes the
host measures.

**What does a decision carry?**

A verb, reason, confidence, optional action and intent, approval, target, evidence and a trail.
