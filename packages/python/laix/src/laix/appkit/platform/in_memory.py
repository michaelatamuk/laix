"""A small in-memory platform for tests and local runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from .approval_decision import ApprovalDecision
from .approval_request import ApprovalRequest
from .capability import Capability
from .event import PlatformEvent
from .skill_call import SkillCall


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class InMemoryPlatform:
    """A small platform for tests and local runs."""

    def __init__(
        self,
        *,
        approver: Callable[[ApprovalRequest], ApprovalDecision] | None = None,
    ) -> None:
        self._skills: dict[str, Callable[[SkillCall], Any]] = {}
        self._state: dict[str, Any] = {}
        self._events: list[PlatformEvent] = []
        self._approver = approver
        self._capabilities = {
            "fast": Capability("fast", ("text",), 200, 0.001),
            "balanced": Capability("balanced", ("text", "image"), 1500, 0.02),
            "deep": Capability("deep", ("text", "image", "audio", "video"), 15000, 0.2),
        }

    def register(self, capability: str, handler: Callable[[SkillCall], Any]) -> None:
        self._skills[capability] = handler

    def run_skill(self, call: SkillCall) -> Any:
        handler = self._skills.get(call.capability)
        if handler is None:
            raise KeyError(f"no skill registered for {call.capability!r}")
        self._events.append(PlatformEvent(call.trace_id, "skill.started", _now(), {"capability": call.capability}))
        result = handler(call)
        self._events.append(PlatformEvent(call.trace_id, "skill.finished", _now(), {"capability": call.capability}))
        return result

    def cancel(self, run_id: str, reason: str = "") -> bool:
        self._events.append(PlatformEvent(run_id, "skill.cancelled", _now(), {"reason": reason}))
        return True

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        if self._approver is not None:
            decision = self._approver(request)
        else:
            decision = ApprovalDecision(approved=False, by="", at=_now(), note="no approver configured")
        self._events.append(
            PlatformEvent(request.decision_id, "approval.decided", _now(), {"approved": decision.approved, "by": decision.by})
        )
        return decision

    def read_state(self, key: str) -> Any:
        return self._state.get(key)

    def write_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def events(self, trace_id: str) -> Iterable[PlatformEvent]:
        return tuple(event for event in self._events if event.trace_id == trace_id)

    def capability(self, level: str) -> Capability:
        try:
            return self._capabilities[level]
        except KeyError as exc:
            raise ValueError(f"unknown capability level: {level!r}") from exc


__all__ = ["InMemoryPlatform"]
