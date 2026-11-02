"""Policies: the built-in action policy, packaged packs and the plugin registry.

The packaged packs are loaded lazily. ``decisions`` imports the registry, and
the packs import ``decisions``; lazy loading keeps that cycle out of import time.
"""

from .action import ACTION_POLICY_VERSION, ActionPolicy, ActionPolicyConfig, ActionPolicyRequest, decide_action
from .registry import Policy, PolicyError, PolicyRegistry

_LAZY = {
    "ActivePerceptionPolicy": "active_perception",
    "AllocationPolicy": "allocation",
    "BanditPolicy": "bandit",
    "EscalationPolicy": "escalation",
    "NegotiationPolicy": "negotiation",
    "PreferenceElicitationPolicy": "preference",
    "ReplanningPolicy": "replanning",
    "SafetyConstrainedPolicy": "safety",
    "VerificationPolicy": "verification",
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
