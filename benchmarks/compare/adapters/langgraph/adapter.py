"""LangGraph adapter: a decision node plus an approval interrupt."""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from pathlib import Path

from laix import PlannerInput, LiveCompositePlanner, PlannerResult

from ..result import AdapterResult
from .state import LangGraphState

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, StateGraph

    _AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _AVAILABLE = False


class LangGraphAdapter:
    """Put the same LAIX composite planner inside a LangGraph state machine."""

    name = "langgraph"
    dependencies = ("langgraph",)

    def __init__(self) -> None:
        self._engine = LiveCompositePlanner()
        self._graph = None
        if _AVAILABLE:
            self._graph = self._build()

    def available(self) -> bool:
        return _AVAILABLE

    def _build(self):
        builder = StateGraph(LangGraphState)
        builder.add_node("decide", self._decide)
        builder.add_node("approval", self._approval)
        builder.set_entry_point("decide")
        builder.add_conditional_edges(
            "decide",
            self._route,
            {"approval": "approval", END: END},
        )
        builder.add_edge("approval", END)
        return builder.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["approval"],
        )

    def _decide(self, state: LangGraphState) -> dict[str, object]:
        plan = self._engine.solve(state["problem"])
        return {"plan": plan, "requires_approval": bool(plan.requires_approval)}

    def _approval(self, state: LangGraphState) -> dict[str, object]:
        return {}

    def _route(self, state: LangGraphState) -> str:
        return "approval" if state.get("requires_approval") else END

    def solve(self, problem: PlannerInput) -> PlannerResult:
        if self._graph is None:
            raise RuntimeError("langgraph is not installed")
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self._graph.invoke({"problem": problem}, config)
        snapshot = self._graph.get_state(config)
        plan = snapshot.values.get("plan")
        if snapshot.next:
            self._graph.invoke({"approved": True}, config)
            plan = self._graph.get_state(config).values.get("plan", plan)
        if plan is None:
            raise RuntimeError("LangGraph did not return a plan")
        return plan

    def run(self, problems: Sequence[PlannerInput]) -> AdapterResult:
        if self._graph is None:
            return AdapterResult(
                name=self.name,
                available=False,
                dependencies=self.dependencies,
                notes=("install langgraph: python -m pip install -r benchmarks/compare/requirements-external.txt",),
            )
        interrupts = 0
        started = time.perf_counter()
        for problem in problems:
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            self._graph.invoke({"problem": problem}, config)
            snapshot = self._graph.get_state(config)
            if snapshot.next:
                interrupts += 1
                self._graph.invoke({"approved": True}, config)
        elapsed = (time.perf_counter() - started) * 1000.0
        glue = len(Path(__file__).read_text(encoding="utf-8").splitlines())
        return AdapterResult(
            name=self.name,
            available=True,
            decisions=len(problems),
            interrupts=interrupts,
            mean_latency_ms=elapsed / len(problems) if problems else 0.0,
            dependencies=self.dependencies,
            glue_lines=glue,
            notes=("same LAIX composite planner inside the graph",),
        )


__all__ = ["LangGraphAdapter"]
