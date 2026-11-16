package dev.laix.decision.contracts

import dev.laix.decision.signals.Signal

/**
 * One request, whichever generic policy the app needs.
 *
 * Provide `situation` and `options` for action selection, or `signals` and
 * `context` for attention allocation. Both paths return [Decision].
 */
data class DecisionRequest(
    val subject: String,
    val at: String,
    val signals: List<Signal> = emptyList(),
    val context: Any? = null,
    val situation: Situation? = null,
    val options: List<ActionOption> = emptyList(),
    val attributes: Map<String, Any?> = emptyMap(),
    val confidence: Double? = null,
    val confidenceSource: String = "",
    val calibrated: Boolean = false,
    val deadline: String? = null,
    val validUntil: String? = null,
    val eventId: String = "",
    val target: TargetMode = TargetMode.ONE,
    val recipients: List<String> = emptyList(),
)
