# LangGraph

LangGraph owns the graph, the checkpoints and the human-in-the-loop pause. LAIX owns the decision:
the verb, reason, score, approval requirement and execution receipt.

| Concern | Owner |
|---|---|
| Graph state, edges and retries | LangGraph |
| Durable checkpoints and `thread_id` | LangGraph checkpointer plus the host database |
| Approval UI and who may approve | The host |
| Verb, reason code, confidence and score | LAIX |
| Execution handlers, idempotency and receipts | The host, through `ExecutionBridge` |
| Audit record and outcome | The host, using the app kit |

This guide uses the Python package and the `LiveCompositePlanner` behind `PlannerPolicy`.

## Install

```powershell
python -m pip install langgraph
python -m pip install "git+https://github.com/michaelatamuk/laix.git@v0.17.0#subdirectory=packages/python/laix"
```

The comparison adapter in `benchmarks/compare/adapters/langgraph/` is optional and is not a
production template. This page is the production shape.

## State

Keep the request, decision, approval and receipt in the graph state. Do not put the whole host
database in it.

```python
from __future__ import annotations

from typing import TypedDict

from laix import Decision, DecisionRequest, ExecutionReceipt


class DecisionState(TypedDict, total=False):
    request: DecisionRequest
    decision: Decision
    approved: bool
    approver: str
    receipt: ExecutionReceipt
```

## The graph

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from laix import (
    ExecutionBridge,
    LiveCompositePlanner,
    PlannerPolicy,
    decide,
)

engine = PlannerPolicy(LiveCompositePlanner())
bridge = ExecutionBridge(handlers={"close case": close_case})  # close_case is a host handler


def decide_node(state: DecisionState) -> dict:
    decision = decide(state["request"], policy=engine)[0]
    return {"decision": decision}


def route_after_decide(state: DecisionState) -> str:
    decision = state["decision"]
    if decision.requires_approval or decision.verb in {"ask", "escalate"}:
        return "approval"
    if decision.verb == "act":
        return "execute"
    return END


def approval_node(state: DecisionState) -> dict:
    # The graph is interrupted before this node. The host writes `approved`.
    return {}


def route_after_approval(state: DecisionState) -> str:
    return "execute" if state.get("approved") else END


def execute_node(state: DecisionState) -> dict:
    decision = state["decision"]
    action = next(
        (option for option in state["request"].options if option.id == decision.action_id),
        None,
    )
    receipt = bridge.execute(
        decision,
        action=action,
        actor="langgraph",
        approver=state.get("approver"),
        idempotency_key=decision.decision_id or None,
    )
    return {"receipt": receipt}


builder = StateGraph(DecisionState)
builder.add_node("decide", decide_node)
builder.add_node("approval", approval_node)
builder.add_node("execute", execute_node)
builder.set_entry_point("decide")
builder.add_conditional_edges(
    "decide",
    route_after_decide,
    {"approval": "approval", "execute": "execute", END: END},
)
builder.add_conditional_edges(
    "approval",
    route_after_approval,
    {"execute": "execute", END: END},
)
builder.add_edge("execute", END)

graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["approval"],
)
```

`MemorySaver` is for development. In production use a durable checkpointer and a stable
`thread_id` per task.

## Run, pause and resume

```python
config = {"configurable": {"thread_id": "case-1"}}

graph.invoke({"request": request}, config)
state = graph.get_state(config)

if "approval" in state.next:
    decision = state.values["decision"]
    # Show decision.verb, reason_code, action_id, rationale and evidence to the approver.
    approved = ask_the_approver(decision)

    graph.update_state(config, {"approved": approved, "approver": "alice"})
    graph.invoke(None, config)

final = graph.get_state(config).values
receipt = final.get("receipt")
```

The approval decision must be durable. Do not keep it only in a process variable. Pass the approver
identity into `execute` so `ExecutionBridge` can enforce the approval gate.

LangGraph serializes graph state. The example stores `DecisionRequest` and `Decision` objects for
readability; in production either register the LAIX types with the checkpointer serializer or keep
only dicts and ids in the state and rebuild the objects inside the nodes.

## What the execute node should do

- Use a stable idempotency key: `decision.decision_id`, `trace_id` or the host event id.
- Pass the chosen `ActionOption`; do not re-derive it from prose.
- Record the `ExecutionReceipt` status: `executed`, `failed`, `unknown`, `duplicate`.
- If the receipt is `unknown`, reconcile with the provider before retrying.
- Never retry an effect without an idempotency key.
- Use `RetryPolicy` or `execute_async` for transient failures and hard timeouts.

## Production wiring

| Piece | Development | Production |
|---|---|---|
| Checkpointer | `MemorySaver` | SQLite, Postgres or the host's durable store |
| Thread id | one per test | one per task or incident |
| Approval | manual resume | durable approval record plus timeout |
| Execution | fake handler | idempotent host skill |
| Receipts | in memory | host store or `FileStateStore` / database port |
| Observability | logs | `decision_attributes(decision)` on the span |
| Retries | none | `RetryPolicy` with capped backoff |
| Timeouts | none | `execute_async(..., timeout_seconds=...)` |

Keep the graph small. The decision node calls LAIX; the execute node calls the host. Do not put
domain logic, database access or transport inside the decision node.

## Test the graph

Use `MemorySaver` and a fake handler:

```python
def test_graph_pauses_for_approval() -> None:
    config = {"configurable": {"thread_id": "test-1"}}
    graph.invoke({"request": request_that_needs_approval}, config)

    state = graph.get_state(config)
    assert "approval" in state.next

    graph.update_state(config, {"approved": True})
    graph.invoke(None, config)

    final = graph.get_state(config).values
    assert final["receipt"].status in {"executed", "duplicate"}
```

## What not to do

- Do not let the graph approve itself by default.
- Do not treat `requires_approval=True` as an approval.
- Do not retry an `unknown` receipt blindly.
- Do not store credentials or raw customer data in the graph state.
- Do not put the decision logic in a LangGraph node; call LAIX and branch on the decision fields.

## Related

- [Integration](01-integration.md) - the adapter boundary.
- [DecisionClient](02-single-decision.md) - `DecisionClient` and the response.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - receipts, retries and timeouts.
- [Metrics](../05-operate/02-metrics.md) - OpenTelemetry attributes.
- [External comparison](../../../benchmarks/compare/README.md) - the benchmark adapter.
