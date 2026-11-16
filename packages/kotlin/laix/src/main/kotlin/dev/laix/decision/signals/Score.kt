package dev.laix.decision.signals

import dev.laix.decision.contracts.ScoreBreakdown
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round
import java.time.OffsetDateTime

val SEVERITY_POINTS: Map<String, Double> =
    linkedMapOf("critical" to 60.0, "high" to 45.0, "medium" to 30.0, "low" to 15.0, "info" to 5.0)

/** How much an hour of silence costs, relative to severity. */
val WAIT_FACTOR: Map<String, Double> =
    linkedMapOf("critical" to 2.0, "high" to 1.5, "medium" to 1.0, "low" to 0.5, "info" to 0.25)

fun duePoints(now: OffsetDateTime, due: String?): Double {
    val hours = hoursUntil(now, due) ?: return 0.0
    return when {
        hours < 0 -> 30.0
        hours <= 24 -> 20.0
        hours <= 72 -> 12.0
        hours <= 168 -> 6.0
        else -> 0.0
    }
}

fun score(signal: Signal, context: SignalContext): ScoreBreakdown {
    val severity = SEVERITY_POINTS[signal.severity] ?: 5.0
    val due = duePoints(context.now, signal.due)
    val confidence = clamp(signal.confidence) * 20.0
    val interruption = -clamp(signal.interruptionCost) * 20.0
    val learned = context.learned[signal.kind] ?: 0.0
    val total = severity + due + confidence + interruption + learned
    return ScoreBreakdown(
        severity = severity,
        due = due,
        confidence = confidence,
        interruption = interruption,
        learned = learned,
        total = total,
    )
}

/** Points at stake if the decision is silence. Zero without a deadline. */
fun costOfWaiting(signal: Signal, context: SignalContext): Double {
    val factor = WAIT_FACTOR[signal.severity] ?: 0.25
    return round(duePoints(context.now, signal.due) * factor, 2)
}
