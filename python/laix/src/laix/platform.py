"""The south interface: what LAIX needs from the platform underneath it.

The app and the platform are different. The app describes the experience; the
platform runs skills, approves destructive actions, keeps session state and
streams events. LAIX names a capability level, never a model name.

This module is a contract and an in-memory reference implementation. A real
platform adapter implements the same protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

CAPABILITY_LEVELS: tuple[str, ...] = ("fast", "balanced", "deep")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class SkillCall:
    capability: str
    args: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    decision_id: str
    action: str
    rationale: str = ""
    risk: float = 0.0
    reversible: bool = True
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approved: bool
    by: str = ""
    at: str = ""
    note: str = ""


@dataclass(frozen=True, slots=True)
class Event:
    trace_id: str
    kind: str
    at: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Capability:
    """A capability level, not a model name."""

    level: str
    modalities: tuple[str, ...] = ()
    max_latency_ms: int | None = None
    max_cost: float | None = None

    def __post_init__(self) -> None:
        if self.level not in CAPABILITY_LEVELS:
            raise ValueError(f"unknown capability level: {self.level!r}")


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

    def events(self, trace_id: str) -> Iterable[Event]:
        ...

    def capability(self, level: str) -> Capability:
        ...


class InMemoryPlatform:
    """A small platform for tests and local runs."""

    def __init__(
        self,
        *,
        approver: Callable[[ApprovalRequest], ApprovalDecision] | None = None,
    ) -> None:
        self._skills: dict[str, Callable[[SkillCall], Any]] = {}
        self._state: dict[str, Any] = {}
        self._events: list[Event] = []
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
        self._events.append(Event(call.trace_id, "skill.started", _now(), {"capability": call.capability}))
        result = handler(call)
        self._events.append(Event(call.trace_id, "skill.finished", _now(), {"capability": call.capability}))
        return result

    def cancel(self, run_id: str, reason: str = "") -> bool:
        self._events.append(Event(run_id, "skill.cancelled", _now(), {"reason": reason}))
        return True

    def request_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        if self._approver is not None:
            decision = self._approver(request)
        else:
            decision = ApprovalDecision(approved=False, by="", at=_now(), note="no approver configured")
        self._events.append(
            Event(request.decision_id, "approval.decided", _now(), {"approved": decision.approved, "by": decision.by})
        )
        return decision

    def read_state(self, key: str) -> Any:
        return self._state.get(key)

    def write_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def events(self, trace_id: str) -> Iterable[Event]:
        return tuple(event for event in self._events if event.trace_id == trace_id)

    def capability(self, level: str) -> Capability:
        try:
            return self._capabilities[level]
        except KeyError as exc:
            raise ValueError(f"unknown capability level: {level!r}") from exc


__all__ = [
    "ApprovalDecision",
    "ApprovalRequest",
    "CAPABILITY_LEVELS",
    "Capability",
    "Event",
    "InMemoryPlatform",
    "Platform",
    "SkillCall",
]
