package dev.laix.decision.support

import dev.laix.decision.contracts.Decision

/** Map one decision onto stable OpenTelemetry attribute names. */
fun decisionAttributes(decision: Decision): Map<String, Any?> {
    val attributes = linkedMapOf<String, Any?>(
        "laix.verb" to decision.verb.value,
        "laix.reason_code" to decision.reasonCode,
        "laix.confidence" to decision.confidence,
        "laix.approval.required" to decision.requiresApproval,
        "laix.reversible" to decision.reversible,
        "laix.status" to decision.status.value,
        "laix.target" to decision.target.value,
        "laix.calibrated" to decision.calibrated,
        "laix.schema.version" to decision.schemaVersion,
    )
    val optional = linkedMapOf<String, Any?>(
        "laix.decision.id" to decision.decisionId,
        "laix.trace.id" to decision.traceId,
        "laix.situation.id" to decision.situationId,
        "laix.action.id" to decision.actionId,
        "laix.policy.version" to decision.policyVersion,
        "laix.confidence.source" to decision.confidenceSource,
        "laix.stream.id" to decision.streamId,
        "laix.supersedes" to decision.supersedes,
        "laix.event.time" to decision.eventTime,
    )
    for ((name, value) in optional) {
        if (value != null && value != "") attributes[name] = value
    }
    decision.score?.let { attributes["laix.score"] = it }
    if (decision.revision != 0) attributes["laix.revision"] = decision.revision
    return attributes
}
