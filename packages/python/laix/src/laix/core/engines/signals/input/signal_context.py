"""Everything the policy needs that is not the signal itself."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .signal_feedback import SignalFeedback


@dataclass(slots=True)
class SignalContext:
    """Everything the policy needs that is not the signal itself."""

    now: datetime
    quiet_hours: tuple[str, str] | None = ("22:00", "06:00")
    mode: str = "shadow"
    stopped: bool = False
    min_severity: str = "high"
    min_confidence: float = 0.0
    muted_kinds: tuple[str, ...] = ()
    # Deliver at most this many signals per decision cycle. None means no cap.
    signal_interruption_budget: int | None = None
    # Dedupe keys already delivered in this period, for example "signal-1:2026-11-14".
    sent: frozenset[str] = frozenset()
    # What the user already said, keyed by signal id.
    feedback: dict[str, SignalFeedback] = field(default_factory=dict)
    # Escalate a critical signal that is older than this many hours. None disables it.
    escalate_after_hours: float | None = None
    # Learned per-kind point adjustment, supplied by the app or a bandit.
    learned: dict[str, float] = field(default_factory=dict)
    # When true and the signal carries a reversible intent, the policy may act
    # or ask instead of only notifying. Off by default.
    allow_act: bool = False


__all__ = ["SignalContext"]
