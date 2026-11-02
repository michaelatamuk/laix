"""One thing that might deserve the user's attention."""

from __future__ import annotations

from dataclasses import dataclass

from ....decisions import Intent


@dataclass(frozen=True, slots=True)
class Signal:
    """One thing that might deserve the user's attention."""

    id: str
    kind: str
    title: str = ""
    detail: str = ""
    severity: str = "low"
    confidence: float = 0.5
    due: str | None = None
    evidence_refs: tuple[str, ...] = ()
    group_key: str | None = None
    interruption_cost: float = 0.0
    requires_approval: bool = False
    #: The action the app is prepared to take. ``None`` means "guide only".
    intent: Intent | None = None
    #: Whether an executed action can be taken back.
    reversible: bool = False
    #: Who to escalate to when the signal stays overdue.
    handover: Intent | None = None


__all__ = ["Signal"]
