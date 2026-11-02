"""Policies: the built-in action policy, packaged packs and the plugin registry.

The packaged packs are loaded lazily. ``decisions`` imports the registry, and
the packs import ``decisions``; lazy loading keeps that cycle out of import time.
"""

from __future__ import annotations

from ..support.errors import PolicyError
from .builtin.action import ACTION_POLICY_VERSION, ActionPolicy, ActionPolicyConfig, ActionPolicyRequest, decide_action
from .policy import Policy
from .registry import PolicyRegistry

_LAZY = {
    "ActivePerceptionPolicy": "packs.active_perception",
    "AllocationPolicy": "packs.allocation",
    "BanditPolicy": "packs.bandit",
    "EscalationPolicy": "packs.escalation",
    "NegotiationPolicy": "packs.negotiation",
    "PreferenceElicitationPolicy": "packs.preference",
    "ReplanningPolicy": "packs.replanning",
    "SafetyConstrainedPolicy": "packs.safety",
    "VerificationPolicy": "packs.verification",
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
