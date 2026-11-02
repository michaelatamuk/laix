"""Auditable thresholds for the built-in action policy."""

from __future__ import annotations

from dataclasses import dataclass

ACTION_POLICY_VERSION = "0.8.0"


@dataclass(frozen=True)
class ActionPolicyConfig:
    """Thresholds are explicit so a host can audit and tune them.

    The defaults reproduce a conservative operating posture: act only when both
    urgency and confidence are high, ask when the evidence is weak, and never
    interrupt for a low-urgency event.
    """

    min_confidence: float = 0.55
    act_confidence: float = 0.80
    ask_uncertainty: float = 0.45
    act_urgency: float = 0.75
    guide_urgency: float = 0.45
    max_risk: float = 0.90
    max_interrupt: float = 0.90
    approval_kinds: tuple[str, ...] = ("approval", "safety")
    max_alternatives: int = 6


__all__ = ["ACTION_POLICY_VERSION", "ActionPolicyConfig"]
