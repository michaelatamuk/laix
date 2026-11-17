package dev.laix.decision

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.DecisionStatus
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.TargetMode
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.action.ActionPolicy
import dev.laix.decision.policies.action.ActionPolicyInput
import dev.laix.decision.signals.SignalAttentionDecision
import dev.laix.decision.signals.SignalContext
import dev.laix.decision.signals.decideSignalAttention
import dev.laix.decision.support.DecisionPolicyError
import dev.laix.decision.support.clamp
import dev.laix.decision.support.newId
import dev.laix.decision.support.truthy

/** Which handler a request is routed to. */
enum class Route {
    POLICY,
    ACTION,
    ATTENTION,
}

/** Name the handler for this request: policy, action or attention. */
fun select(request: DecisionRequest, policy: DecisionPolicy? = null): Route {
    if (policy != null) return Route.POLICY
    if (request.situation != null || request.options.isNotEmpty()) return Route.ACTION
    if (request.signals.isNotEmpty() || request.context != null) return Route.ATTENTION
    throw IllegalArgumentException("request has neither a situation/options nor signals/context")
}

/** Merge the request's confidence fields into policy attributes. */
fun attributesFor(request: DecisionRequest): Map<String, Any?> {
    val attributes = LinkedHashMap(request.attributes)
    request.confidence?.let { attributes.putIfAbsent("confidence", it) }
    if (request.confidenceSource.isNotEmpty()) {
        attributes.putIfAbsent("confidence_source", request.confidenceSource)
    }
    if (request.calibrated) {
        attributes.putIfAbsent("calibrated", true)
    }
    return attributes
}

/** Carry the request's confidence provenance onto a decision. */
fun annotateConfidence(decision: Decision, request: DecisionRequest): Decision {
    val source = request.confidenceSource.ifEmpty { decision.confidenceSource }
    val calibrated = request.calibrated || decision.calibrated
    if (source == decision.confidenceSource && calibrated == decision.calibrated) {
        return decision
    }
    return decision.copy(confidenceSource = source, calibrated = calibrated)
}

/**
 * Return decisions without the app kit.
 *
 * Pass `policy` to use a specific policy. Otherwise the request shape selects
 * the built-in action policy or signal attention. Every decision gets a
 * `decisionId`; a `traceId` is generated when the planner did not provide one.
 */
fun decide(
    request: DecisionRequest,
    policy: DecisionPolicy? = null,
    idFactory: (String) -> String = ::newId,
): List<Decision> =
    when (select(request, policy)) {
        Route.POLICY -> policy!!.decide(request).map {
            annotateConfidence(identify(it, idFactory), request)
        }

        Route.ACTION -> {
            val situation = request.situation
                ?: throw IllegalArgumentException("action selection needs a situation")
            val actionRequest = ActionPolicyInput(
                situation = situation,
                options = request.options,
                attributes = attributesFor(request),
            )
            listOf(
                annotateConfidence(
                    identify(ActionPolicy().decide(actionRequest), idFactory),
                    request,
                ),
            )
        }

        Route.ATTENTION -> {
            val context = request.context as? SignalContext
                ?: throw IllegalArgumentException("attention allocation needs a context with now")
            decideSignalAttention(request.signals, context).map {
                annotateConfidence(identify(fromSignalAttention(it), idFactory), request)
            }
        }
    }

/** Convert a signal-attention decision to the one public decision shape. */
fun fromSignalAttention(decision: SignalAttentionDecision): Decision =
    Decision(
        verb = decision.verb,
        confidence = clamp(decision.confidence),
        reasonCode = decision.reasonCode,
        rationale = decision.reasonCode,
        evidence = decision.evidenceRefs.map { EvidenceRef(id = it) },
        requiresApproval = decision.requiresApproval,
        score = decision.score,
        breakdown = decision.breakdown,
        intent = decision.intent,
        costOfWaiting = decision.costOfWaiting,
        reversible = decision.reversible,
        undoHint = decision.undoHint,
        traceId = decision.traceId,
        deliver = decision.deliver,
        record = decision.record,
    )

/** Normalise a policy result to the one public decision shape. */
fun coerce(value: Any?): Decision =
    when (value) {
        is Decision -> value
        is SignalAttentionDecision -> fromSignalAttention(value)
        is Map<*, *> -> decisionFromMap(value)
        else -> throw DecisionPolicyError(
            "policy returned an unsupported decision: " +
                (value?.let { it::class.simpleName } ?: "null"),
        )
    }

private fun identify(decision: Decision, makeId: (String) -> String): Decision {
    var result = decision
    if (result.decisionId.isEmpty()) result = result.copy(decisionId = makeId("DEC"))
    if (result.traceId.isEmpty()) result = result.copy(traceId = makeId("TRC"))
    return result
}

@Suppress("UNCHECKED_CAST")
private fun decisionFromMap(value: Map<*, *>): Decision {
    fun text(key: String): String? = value[key]?.toString()
    fun bool(key: String, default: Boolean): Boolean =
        value[key]?.let { truthy(it) } ?: default

    return Decision(
        verb = Verb.from(text("verb")?.takeIf { it.isNotEmpty() } ?: Verb.WAIT.value),
        confidence = clamp((value["confidence"] as? Number)?.toDouble() ?: 0.0),
        reasonCode = text("reason_code")?.takeIf { it.isNotEmpty() } ?: "policy_rule",
        rationale = text("rationale") ?: "",
        decisionId = text("decision_id") ?: "",
        requiresApproval = bool("requires_approval", false),
        score = (value["score"] as? Number)?.toDouble(),
        traceId = text("trace_id") ?: "",
        deliver = bool("deliver", true),
        record = bool("record", true),
        streamId = text("stream_id") ?: "",
        eventTime = text("event_time"),
        deadline = text("deadline"),
        validUntil = text("valid_until"),
        supersedes = text("supersedes"),
        revision = (value["revision"] as? Number)?.toInt() ?: 0,
        status = DecisionStatus.from(text("status") ?: DecisionStatus.FINAL.value),
        target = TargetMode.from(text("target") ?: TargetMode.ONE.value),
        recipients = (value["recipients"] as? List<*>)?.map { it.toString() } ?: emptyList(),
    )
}
