"""Policies: the built-in action policy, the other policies and the plugin registry.

The other policies are loaded lazily. ``decisions`` imports the registry, and
the policies import ``decisions``; lazy loading keeps that cycle out of import time.
"""

from __future__ import annotations

from ...support.errors import PolicyError
from .implementations.action import ACTION_POLICY_VERSION, ActionPolicy, ActionPolicyConfig, ActionPolicyRequest, decide_action
from .policy import Policy
from .registry import PolicyRegistry

_LAZY = {
    "ActivePerceptionPolicy": "implementations.active_perception",
    "AllocationPolicy": "implementations.allocation",
    "BanditPolicy": "implementations.bandit",
    "EscalationPolicy": "implementations.escalation",
    "NegotiationPolicy": "implementations.negotiation",
    "PreferenceElicitationPolicy": "implementations.preference_elicitation",
    "ReplanningPolicy": "implementations.replanning",
    "SafetyConstrainedPolicy": "implementations.safety_constrained",
    "VerificationPolicy": "implementations.verification",
    "Rule": "implementations.rules",
    "RulePolicy": "implementations.rules",
    "TargetedPolicy": "implementations.target",
}


def __getattr__(name: str):
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    return getattr(import_module(f".{module}", __name__), name)


__all__ = [
    "ActivePerceptionPolicy",
    "AllocationPolicy",
    "BanditPolicy",
    "ActionPolicy",
    "EscalationPolicy",
    "NegotiationPolicy",
    "PreferenceElicitationPolicy",
    "ReplanningPolicy",
    "SafetyConstrainedPolicy",
    "VerificationPolicy",
    "Rule",
    "RulePolicy",
    "TargetedPolicy",
    "ACTION_POLICY_VERSION",
    "Policy",
    "ActionPolicyConfig",
    "PolicyError",
    "PolicyRegistry",
    "ActionPolicyRequest",
    "decide_action",
]
