"""The south interface: what LAIX needs from the platform underneath it."""

from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable

from .approval_decision import ApprovalDecision
from .approval_request import ApprovalRequest
from .capability import Capability
from .event import PlatformEvent
from .skill_call import SkillCall


@runtime_checkable
class Platform(Protocol):
    def run_skill(self, call: SkillCall) -> Any:
        ...

    def cancel(self, run_id: str, reason: str = "") -> bool:
        ...

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        ...

    def read_state(self, key: str) -> Any:
        ...

    def write_state(self, key: str, value: Any) -> None:
        ...

    def events(self, trace_id: str) -> Iterable[PlatformEvent]:
        ...

    def capability(self, level: str) -> Capability:
        ...


__all__ = ["Platform"]
