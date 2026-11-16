/**
 * Generated from packages/contracts/reason-codes.v1.json. Do not edit by hand.
 */

package dev.laix.decision.contract

import dev.laix.decision.contracts.SCHEMA_VERSION

object ReasonCodes {
    const val VERSION: String = "1.1.0"

    const val NOTE: String =
        "Authored rules may define their own reason_code. Treat an unknown code as policy-specific rather than silently mapping it."

    val SIGNAL_ATTENTION: List<String> = listOf(
        "worth_surfacing",
        "kill_switch",
        "muted",
        "snoozed",
        "wrong",
        "assigned",
        "dismissed",
        "low_confidence",
        "below_floor",
        "already_sent",
        "quiet_hours",
        "budget",
        "overdue_escalation",
        "act",
        "ask_approval",
    )

    val PLANNER: List<String> = listOf(
        "approval_rejected",
        "case_based",
        "commitment_aware",
        "commitment_belief",
        "commitment_belief_verify",
        "commitment_resolution",
        "decision_escalated",
        "decision_held",
        "decision_revised",
        "execution_aware",
        "expected_utility",
        "goal_conflict",
        "goal_conflict_needs_choice",
        "goal_conflict_resolved",
        "human_attention_aware",
        "human_attention_budget_exhausted",
        "live_decision",
        "mdp_plan",
        "no_action",
        "no_case",
        "no_feasible_option",
        "no_goal_conflict",
        "no_options",
        "pomdp_plan",
        "revalidated_new",
        "risk_bounded",
        "terminal_state",
        "value_of_decision",
    )

    val POLICY: List<String> = listOf(
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
    )

    val APPKIT: List<String> = listOf(
        "execution_step",
    )

    val BENCH: List<String> = listOf(
        "fixed_action",
    )

    val GROUPS: Map<String, List<String>> = linkedMapOf(
        "signal_attention" to SIGNAL_ATTENTION,
        "planner" to PLANNER,
        "policy" to POLICY,
        "appkit" to APPKIT,
        "bench" to BENCH,
    )

    val CODES: List<String> = GROUPS.values.flatten().distinct().sorted()

    fun registry(): Map<String, Any> = linkedMapOf(
        "version" to VERSION,
        "schema_version" to SCHEMA_VERSION,
        "extensible" to true,
        "note" to NOTE,
        "groups" to GROUPS,
        "codes" to CODES,
    )
}
