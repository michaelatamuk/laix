package dev.laix.decision.policies.action

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Situation

/**
 * Thresholds are explicit so a host can audit and tune them.
 *
 * The defaults reproduce a conservative operating posture: act only when both
 * urgency and confidence are high, ask when the evidence is weak, and never
 * interrupt for a low-urgency event.
 */
data class ActionPolicyConfig(
    val minConfidence: Double = 0.55,
    val actConfidence: Double = 0.80,
    val askUncertainty: Double = 0.45,
    val actUrgency: Double = 0.75,
    val guideUrgency: Double = 0.45,
    val maxRisk: Double = 0.90,
    val maxInterrupt: Double = 0.90,
    val approvalKinds: List<String> = listOf("approval", "safety"),
    val maxAlternatives: Int = 6,
)

/** Input for one action-policy decision. */
data class ActionPolicyInput(
    val situation: Situation,
    val options: List<ActionOption> = emptyList(),
    val attributes: Map<String, Any?> = emptyMap(),
)
