"""The stable reason-code registry.

Reason codes are part of the decision contract. App logic branches on them, so a
rename is a behaviour change. This module is the source of truth for the flat
registry published as ``packages/contracts/reason-codes.v1.json``.
"""

from __future__ import annotations

from typing import Any

from ..support.version import SCHEMA_VERSION

REASON_CODES_VERSION = "1.0.0"

#: Authored rules may add their own code. Everything else is enumerated here.
REASON_CODE_GROUPS: dict[str, tuple[str, ...]] = {
    "planner": (
        "approval_rejected",
        "commitment_aware",
        "execution_aware",
        "expected_utility",
        "human_attention_aware",
        "human_attention_budget_exhausted",
        "live_decision",
        "mdp_plan",
        "no_action",
        "no_feasible_option",
        "no_options",
        "pomdp_plan",
        "terminal_state",
        "value_of_decision",
    ),
    "policy": (
        "accept_offer",
        "allocate",
        "already_verified",
        "ask_preference",
        "bandit_choice",
        "counter_offer",
        "escalate_to_target",
        "no_arm_within_limits",
        "no_arms",
        "no_feasible_plan",
        "no_observation",
        "no_question",
        "no_rule",
        "no_safe_option",
        "no_verification_budget",
        "no_verification_path",
        "nothing_affordable",
        "observation_not_worth_it",
        "observe_for_information",
        "policy_rule",
        "preference_known",
        "replan",
        "resolved",
        "round_limit",
        "safe_action",
        "safe_to_show",
        "safety_blocked",
        "target_required",
        "uncertainty_low",
        "verification_not_needed",
        "verify_outcome",
        "within_limits",
    ),
    "appkit": ("execution_step",),
    "bench": ("fixed_action",),
}


def reason_code_registry() -> dict[str, Any]:
    """Return the versioned registry, with signal attention read from its enum."""
    from ..engines.sensing.signals.gates.reason import REASONS

    groups = {
        "signal_attention": tuple(REASONS),
        **{name: tuple(codes) for name, codes in REASON_CODE_GROUPS.items()},
    }
    codes = sorted({code for group in groups.values() for code in group})
    return {
        "version": REASON_CODES_VERSION,
        "schema_version": SCHEMA_VERSION,
        "extensible": True,
        "note": (
            "Authored rules may define their own reason_code. Treat an unknown "
            "code as policy-specific rather than silently mapping it."
        ),
        "groups": {name: list(group) for name, group in groups.items()},
        "codes": codes,
    }


__all__ = [
    "REASON_CODE_GROUPS",
    "REASON_CODES_VERSION",
    "reason_code_registry",
]
