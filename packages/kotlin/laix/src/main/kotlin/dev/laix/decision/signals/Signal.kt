package dev.laix.decision.signals

import dev.laix.decision.contracts.Intent

/** One thing that might deserve the user's attention. */
data class Signal(
    val id: String,
    val kind: String,
    val title: String = "",
    val detail: String = "",
    val severity: String = "low",
    val confidence: Double = 0.5,
    val due: String? = null,
    val evidenceRefs: List<String> = emptyList(),
    val groupKey: String? = null,
    val interruptionCost: Double = 0.0,
    val requiresApproval: Boolean = false,
    /** The action the app is prepared to take. `null` means "guide only". */
    val intent: Intent? = null,
    /** Whether an executed action can be taken back. */
    val reversible: Boolean = false,
    /** Who to escalate to when the signal stays overdue. */
    val handover: Intent? = null,
)

/** A quiet window, inclusive on both ends. */
data class QuietHours(
    val start: String,
    val end: String,
) {
    companion object {
        /** Accept [QuietHours], `("22:00", "06:00")`, `["22:00", "06:00"]` or `"22:00-06:00"`. */
        fun parse(raw: Any?): QuietHours? =
            when (raw) {
                null -> null
                is QuietHours -> raw
                is Pair<*, *> -> QuietHours(raw.first.toString(), raw.second.toString())
                is List<*> ->
                    if (raw.size == 2) QuietHours(raw[0].toString(), raw[1].toString()) else null
                else -> {
                    val text = raw.toString().trim()
                    if ('-' !in text) {
                        null
                    } else {
                        val start = text.substringBefore('-').trim()
                        val end = text.substringAfter('-').trim()
                        if (start.isEmpty() || end.isEmpty()) null else QuietHours(start, end)
                    }
                }
            }
    }
}

/** What the user has already said about this signal. */
data class SignalFeedback(
    val state: String,
    val at: String? = null,
    val until: String? = null,
    val note: String? = null,
)

val FEEDBACK_STATES: List<String> = listOf("accepted", "dismissed", "snoozed", "wrong", "assigned")

/** Severity ordering: lower is more severe. */
val SEVERITY_RANK: Map<String, Int> =
    linkedMapOf("critical" to 0, "high" to 1, "medium" to 2, "low" to 3, "info" to 4)

fun rank(severity: String): Int = SEVERITY_RANK[severity] ?: 9

/** Everything the policy needs that is not the signal itself. */
data class SignalContext(
    val now: java.time.OffsetDateTime,
    val quietHours: QuietHours? = QuietHours("22:00", "06:00"),
    val mode: String = "shadow",
    val stopped: Boolean = false,
    val minSeverity: String = "high",
    val minConfidence: Double = 0.0,
    val mutedKinds: List<String> = emptyList(),
    /** Deliver at most this many signals per decision cycle. `null` means no cap. */
    val signalInterruptionBudget: Int? = null,
    /** Dedupe keys already delivered in this period, for example "signal-1:2026-11-14". */
    val sent: Set<String> = emptySet(),
    /** What the user already said, keyed by signal id. */
    val feedback: Map<String, SignalFeedback> = emptyMap(),
    /** Escalate a critical signal that is older than this many hours. `null` disables it. */
    val escalateAfterHours: Double? = null,
    /** Learned per-kind point adjustment, supplied by the app or a bandit. */
    val learned: Map<String, Double> = emptyMap(),
    /**
     * When true and the signal carries a reversible intent, the policy may act
     * or ask instead of only notifying. Off by default.
     */
    val allowAct: Boolean = false,
)
