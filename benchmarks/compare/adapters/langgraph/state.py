"""State carried through the LangGraph comparison adapter."""

from __future__ import annotations

from typing import Any, TypedDict


class LangGraphState(TypedDict, total=False):
    """One problem and the plan produced by the decision node."""

    problem: Any
    plan: Any
    requires_approval: bool
    approved: bool


__all__ = ["LangGraphState"]
