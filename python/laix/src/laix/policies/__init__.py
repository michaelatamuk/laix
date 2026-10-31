"""Policies: the built-in action policy, reference packs and the plugin registry.

The reference packs are loaded lazily. ``decisions`` imports the registry, and
the packs import ``decisions``; lazy loading keeps that cycle out of import time.
"""

from .action import POLICY_VERSION, DecisionPolicy, PolicyConfig, PolicyRequest, decide
from .registry import Policy, PolicyError, PolicyRegistry

_LAZY = {
    "ActivePerceptionPolicy": "active_perception",
    "AllocationPolicy": "allocation",
    "NegotiationPolicy": "negotiation",
    "PreferenceElicitationPolicy": "preference",
    "ReplanningPolicy": "replanning",
    "SafetyConstrainedPolicy": "safety",
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
    "DecisionPolicy",
    "NegotiationPolicy",
    "PreferenceElicitationPolicy",
    "ReplanningPolicy",
    "SafetyConstrainedPolicy",
    "POLICY_VERSION",
    "Policy",
    "PolicyConfig",
    "PolicyError",
    "PolicyRegistry",
    "PolicyRequest",
    "decide",
]
