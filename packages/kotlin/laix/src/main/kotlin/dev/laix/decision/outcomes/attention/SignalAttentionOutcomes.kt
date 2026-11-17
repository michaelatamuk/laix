package dev.laix.decision.outcomes.attention

import dev.laix.decision.contracts.Verb
import dev.laix.decision.outcomes.OUTCOME_LABELS
import dev.laix.decision.outcomes.OutcomeLabel
import dev.laix.decision.support.round

val RESULTS: List<String> = OUTCOME_LABELS

val REASON_CODES: List<String> = listOf(
    "false_alarm",
    "design_change",
    "operational",
    "duplicate",
    "no_action",
    "data_error",
)

private val HURT_CODES = setOf("false_alarm", "data_error")
private val NEUTRAL_CODES = setOf("design_change", "operational", "duplicate", "no_action")

/** Map an app's dismissal reason to a learning label. */
fun resultForReason(reasonCode: String?): OutcomeLabel {
    if (reasonCode.isNullOrBlank()) return OutcomeLabel.UNKNOWN
    val code = reasonCode.trim().lowercase()
    if (code in HURT_CODES) return OutcomeLabel.HURT
    if (code in NEUTRAL_CODES) return OutcomeLabel.NEUTRAL
    return OutcomeLabel.UNKNOWN
}

/** A UI feedback state (accepted, dismissed, snoozed, wrong) to a result. */
fun labelForFeedback(state: String, reasonCode: String? = null): OutcomeLabel =
    when (state.trim().lowercase()) {
        "accepted", "confirmed", "signed" -> OutcomeLabel.HELPED
        "wrong", "false_alarm" -> OutcomeLabel.HURT
        "dismissed", "snoozed", "assigned" -> resultForReason(reasonCode)
        else -> OutcomeLabel.UNKNOWN
    }

/** What happened after a signal-attention decision. */
data class SignalAttentionOutcome(
    val signalId: String,
    val kind: String,
    val verb: Verb,
    val result: OutcomeLabel,
    val reasonCode: String? = null,
    val score: Double? = null,
    val at: String? = null,
) {
    fun asMap(): Map<String, Any?> =
        linkedMapOf(
            "signal_id" to signalId,
            "kind" to kind,
            "verb" to verb.value,
            "result" to result.value,
            "reason_code" to reasonCode,
            "score" to score,
            "at" to at,
        )
}

/** A bounded, serialisable log. No database, no clock, no app types. */
class SignalAttentionLog(
    val limit: Int = 500,
    val records: MutableList<SignalAttentionOutcome> = mutableListOf(),
) {
    fun record(outcome: SignalAttentionOutcome) {
        records += outcome
        if (records.size > limit) {
            repeat(records.size - limit) { records.removeAt(0) }
        }
    }

    fun extend(outcomes: Iterable<SignalAttentionOutcome>) {
        outcomes.forEach { record(it) }
    }

    private fun counts(kind: String? = null): Map<OutcomeLabel, Int> {
        val counts = linkedMapOf(
            OutcomeLabel.HELPED to 0,
            OutcomeLabel.NEUTRAL to 0,
            OutcomeLabel.HURT to 0,
            OutcomeLabel.UNKNOWN to 0,
        )
        for (item in records) {
            if (kind != null && item.kind != kind) continue
            counts[item.result] = (counts[item.result] ?: 0) + 1
        }
        return counts
    }

    fun total(kind: String? = null): Int = counts(kind).values.sum()

    /** Confirmed / raised. `null` when there is no evidence yet. */
    fun precision(kind: String? = null): Double? {
        val counts = counts(kind)
        val total = counts.values.sum()
        if (total == 0) return null
        return counts.getValue(OutcomeLabel.HELPED).toDouble() / total
    }

    /** Raised actions that turned out wrong. */
    fun hazardRate(kind: String? = null): Double? {
        val counts = counts(kind)
        val total = counts.values.sum()
        if (total == 0) return null
        return counts.getValue(OutcomeLabel.HURT).toDouble() / total
    }

    /** A small per-kind point adjustment for `SignalContext.learned`. */
    fun adjustment(kind: String, weight: Double = 12.0): Double {
        val counts = counts(kind)
        val total = counts.values.sum()
        if (total == 0) return 0.0
        val net = (
            counts.getValue(OutcomeLabel.HELPED) - counts.getValue(OutcomeLabel.HURT)
            ).toDouble() / total
        return round(net * weight, 2)
    }

    /** Observed help rate per score bucket. */
    fun calibration(): List<Map<String, Any?>> {
        val buckets = listOf(0 to 25, 25 to 50, 50 to 75, 75 to 101)
        return buckets.map { (low, high) ->
            val sample = records.filter {
                it.score != null && it.score!! >= low && it.score!! < high
            }
            val helped = sample.count { it.result == OutcomeLabel.HELPED }
            linkedMapOf(
                "low" to low,
                "high" to high,
                "n" to sample.size,
                "helped" to helped,
                "rate" to if (sample.isNotEmpty()) round(helped.toDouble() / sample.size, 3) else 0.0,
            )
        }
    }

    fun byKind(): Map<String, Map<String, Any?>> {
        val kinds = records.map { it.kind }.toSortedSet()
        return kinds.associateWith { kind ->
            val counts = counts(kind)
            linkedMapOf<String, Any?>(
                OutcomeLabel.HELPED.value to counts.getValue(OutcomeLabel.HELPED),
                OutcomeLabel.NEUTRAL.value to counts.getValue(OutcomeLabel.NEUTRAL),
                OutcomeLabel.HURT.value to counts.getValue(OutcomeLabel.HURT),
                OutcomeLabel.UNKNOWN.value to counts.getValue(OutcomeLabel.UNKNOWN),
                "precision" to precision(kind),
                "hazard" to hazardRate(kind),
                "adjustment" to adjustment(kind),
            )
        }
    }
}
