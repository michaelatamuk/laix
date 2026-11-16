package dev.laix.decision.signals

import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.ScoreBreakdown
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.round
import java.security.MessageDigest
import java.time.OffsetDateTime

/** What the signal-attention policy recommends for one signal, and why. */
data class SignalAttentionDecision(
    val signalId: String,
    val verb: Verb,
    val score: Double,
    val reasonCode: String,
    val confidence: Double,
    val deliver: Boolean,
    val record: Boolean,
    val requiresApproval: Boolean,
    val evidenceRefs: List<String>,
    val breakdown: ScoreBreakdown,
    val traceId: String,
    /** Carried for `act` and `ask`; `null` otherwise. */
    val intent: Intent? = null,
    /** Points at stake per hour of silence. 0 when there is no deadline. */
    val costOfWaiting: Double = 0.0,
    /** Whether the requested action can be taken back. */
    val reversible: Boolean = false,
    /** What the app can offer: "withdraw", "cancel", or nothing. */
    val undoHint: String? = null,
) {
    fun asDict(): Map<String, Any?> =
        linkedMapOf(
            "signal_id" to signalId,
            "verb" to verb.value,
            "score" to round(score, 2),
            "reason_code" to reasonCode,
            "confidence" to round(confidence, 3),
            "deliver" to deliver,
            "record" to record,
            "requires_approval" to requiresApproval,
            "evidence_refs" to evidenceRefs,
            "trace_id" to traceId,
            "breakdown" to breakdown.asDict(),
            "intent" to intent?.asDict(),
            "cost_of_waiting" to round(costOfWaiting, 2),
            "reversible" to reversible,
            "undo_hint" to undoHint,
        )
}

/** A stable trace id for one signal, day and verb. */
fun traceId(signal: Signal, now: OffsetDateTime, verb: Verb): String {
    val raw = "${signal.id}|${now.toLocalDate()}|${verb.value}"
    val digest = MessageDigest.getInstance("SHA-1").digest(raw.toByteArray(Charsets.UTF_8))
    return "tr-" + digest.joinToString("") { "%02x".format(it.toInt() and 0xFF) }.take(12)
}

/** How the host can undo an attention decision. */
fun undoHint(verb: Verb, reversible: Boolean): String? =
    when (verb) {
        Verb.GUIDE, Verb.ASK -> "withdraw"
        Verb.ACT -> if (reversible) "cancel" else null
        else -> null
    }

/** Decide one signal by walking [GATE_RULES] in order. */
fun decideOne(
    signal: Signal,
    context: SignalContext,
    delivered: Int = 0,
): SignalAttentionDecision {
    val breakdown = score(signal, context)
    val blocked = feedbackBlocks(context.feedback[signal.id], context.now)

    var result: GateResult? = null
    for ((_, rule) in GATE_RULES) {
        result = rule(signal, context, blocked, delivered)
        if (result != null) break
    }
    val outcome = result
        ?: GateResult(Verb.GUIDE, ReasonCode.WORTH_SURFACING.value, true, true)

    val verb = outcome.verb
    val intent = when (verb) {
        Verb.ESCALATE -> signal.handover
        Verb.ACT, Verb.ASK -> signal.intent
        else -> null
    }

    return SignalAttentionDecision(
        signalId = signal.id,
        verb = verb,
        score = breakdown.total,
        reasonCode = outcome.reasonCode,
        confidence = signal.confidence,
        deliver = outcome.deliver,
        record = outcome.record,
        requiresApproval = signal.requiresApproval,
        evidenceRefs = signal.evidenceRefs,
        breakdown = breakdown,
        traceId = traceId(signal, context.now, verb),
        intent = intent,
        costOfWaiting = costOfWaiting(signal, context),
        reversible = signal.reversible,
        undoHint = undoHint(verb, signal.reversible),
    )
}

/** Return one decision per signal, in input order. */
fun decideSignalAttention(
    signals: Iterable<Signal>,
    context: SignalContext,
): List<SignalAttentionDecision> {
    val out = mutableListOf<SignalAttentionDecision>()
    var delivered = 0
    for (signal in signals) {
        val decision = decideOne(signal, context, delivered)
        if (decision.deliver) delivered += 1
        out += decision
    }
    return out
}

/** The most severe signals first, then the soonest due. Used for digests. */
fun rollup(signals: List<Signal>, limit: Int = 5): List<Signal> =
    signals
        .sortedWith(compareBy({ rank(it.severity) }, { it.due ?: "9999" }))
        .take(limit)
