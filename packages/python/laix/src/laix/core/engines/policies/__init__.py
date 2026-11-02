"""Policies: the built-in action policy, other policies and the plugin registry.

The other policies are loaded lazily. ``decisions`` imports the registry, and
the policies import ``decisions``; lazy loading keeps that cycle out of import time.
"""

from __future__ import annotations

from ...support.errors import PolicyError
from .action import ACTION_POLICY_VERSION, ActionPolicy, ActionPolicyConfig, ActionPolicyRequest, decide_action
from .policy import Policy
from .registry import PolicyRegistry

_LAZY = {
    "ActivePerceptionPolicy": "others.active_perception",
    "AllocationPolicy": "others.allocation",
    "BanditPolicy": "others.bandit",
    "EscalationPolicy": "others.escalation",
    "NegotiationPolicy": "others.negotiation",
    "PreferenceElicitationPolicy": "others.preference",
    "ReplanningPolicy": "others.replanning",
    "SafetyConstrainedPolicy": "others.safety",
    "VerificationPolicy": "others.verification",
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
    "ACTION_POLICY_VERSION",
    "Policy",
    "ActionPolicyConfig",
    "PolicyError",
    "PolicyRegistry",
    "ActionPolicyRequest",
    "decide_action",
]
