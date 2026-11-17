package dev.laix.decision.policies.packs

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round

internal fun policyValue(request: DecisionRequest, key: String, default: Any? = null): Any? =
    request.attributes[key] ?: default

internal fun policyNumber(request: DecisionRequest, key: String, default: Double): Double =
    when (val value = policyValue(request, key, default)) {
        is Number -> value.toDouble()
        is String -> value.toDoubleOrNull() ?: default
        else -> default
    }

@Suppress("UNCHECKED_CAST")
internal fun policyMaps(value: Any?): List<Map<String, Any?>> =
    (value as? Iterable<*>)?.mapNotNull { item ->
        (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
    } ?: emptyList()

internal fun mapNumber(map: Map<String, Any?>, key: String, default: Double = 0.0): Double =
    when (val value = map[key]) {
        is Number -> value.toDouble()
        is String -> value.toDoubleOrNull() ?: default
        else -> default
    }

internal fun mapText(map: Map<String, Any?>, key: String, default: String = ""): String =
    map[key]?.toString() ?: default

internal fun policyDecision(
    policy: String,
    verb: Verb,
    reasonCode: String,
    rationale: String,
    confidence: Double,
    intent: Intent? = null,
    score: Double? = null,
    requiresApproval: Boolean = false,
    actionId: String? = null,
): Decision =
    Decision(
        verb = verb,
        confidence = clamp(confidence),
        reasonCode = reasonCode,
        rationale = rationale,
        policyVersion = policy,
        actionId = actionId,
        requiresApproval = requiresApproval,
        score = score,
        intent = intent,
    )

internal fun round6(value: Double): Double = round(value, 6)
