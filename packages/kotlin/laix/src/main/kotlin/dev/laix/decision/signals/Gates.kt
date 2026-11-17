package dev.laix.decision.signals

import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.parseIso
import java.time.OffsetDateTime

/** A named check. The order lives in [GATE_RULES]. */
enum class Gate(val value: String) {
    KILL_SWITCH("kill_switch"),
    MUTED("muted"),
    FEEDBACK("feedback"),
    LOW_CONFIDENCE("low_confidence"),
    BELOW_FLOOR("below_floor"),
    ALREADY_SENT("already_sent"),
    QUIET_HOURS("quiet_hours"),
    BUDGET("budget"),
    OVERDUE_ESCALATION("overdue_escalation"),
    ACT("act"),
}

/** Every reason an attention decision can carry. */
enum class ReasonCode(val value: String) {
    WORTH_SURFACING("worth_surfacing"),
    KILL_SWITCH("kill_switch"),
    MUTED("muted"),
    SNOOZED("snoozed"),
    WRONG("wrong"),
    ASSIGNED("assigned"),
    DISMISSED("dismissed"),
    LOW_CONFIDENCE("low_confidence"),
    BELOW_FLOOR("below_floor"),
    ALREADY_SENT("already_sent"),
    QUIET_HOURS("quiet_hours"),
    BUDGET("budget"),
    OVERDUE_ESCALATION("overdue_escalation"),
    ACT("act"),
    ASK_APPROVAL("ask_approval"),
}

/** Every reason a decision can carry. A vector file may not invent one. */
val REASONS: List<String> = ReasonCode.entries.map { it.value }

/** A feedback state that suppresses a signal, mapped to its reason. */
val FEEDBACK_REASONS: Map<String, ReasonCode> =
    linkedMapOf(
        "snoozed" to ReasonCode.SNOOZED,
        "wrong" to ReasonCode.WRONG,
        "assigned" to ReasonCode.ASSIGNED,
        "dismissed" to ReasonCode.DISMISSED,
    )

/** The verb, reason and two delivery flags chosen by one gate. */
data class GateResult(
    val verb: Verb,
    val reasonCode: String,
    val record: Boolean,
    val deliver: Boolean,
)

typealias GateRule = (Signal, SignalContext, ReasonCode?, Int) -> GateResult?

/** One interruption per signal per day, by default. */
fun dedupeKey(signal: Signal, now: OffsetDateTime): String =
    "${signal.id}:${now.toLocalDate()}"

/** A snooze with no expiry, or one we cannot read, keeps the signal silent. */
fun snoozedUntilFuture(until: String?, now: OffsetDateTime): Boolean {
    if (until.isNullOrBlank()) return true
    val moment = parseIso(until) ?: return true
    return moment.toInstant() > now.toInstant()
}

/** Return the blocking reason, or `null` when the signal may proceed. */
fun feedbackBlocks(feedback: SignalFeedback?, now: OffsetDateTime): ReasonCode? {
    if (feedback == null || feedback.state == "accepted") return null
    if (feedback.state == "snoozed") {
        return if (snoozedUntilFuture(feedback.until, now)) ReasonCode.SNOOZED else null
    }
    return FEEDBACK_REASONS[feedback.state]
}

private val killSwitch: GateRule = { _, context, _, _ ->
    if (context.stopped) {
        GateResult(Verb.WAIT, ReasonCode.KILL_SWITCH.value, false, false)
    } else {
        null
    }
}

private val muted: GateRule = { signal, context, _, _ ->
    if (signal.kind in context.mutedKinds) {
        GateResult(Verb.WAIT, ReasonCode.MUTED.value, false, false)
    } else {
        null
    }
}

private val feedback: GateRule = { _, _, blocked, _ ->
    blocked?.let { GateResult(Verb.WAIT, it.value, false, false) }
}

private val lowConfidence: GateRule = { signal, context, _, _ ->
    if (signal.confidence < context.minConfidence) {
        GateResult(Verb.WAIT, ReasonCode.LOW_CONFIDENCE.value, false, false)
    } else {
        null
    }
}

private val belowFloor: GateRule = { signal, context, _, _ ->
    if (rank(signal.severity) > rank(context.minSeverity)) {
        GateResult(Verb.WAIT, ReasonCode.BELOW_FLOOR.value, false, false)
    } else {
        null
    }
}

private val alreadySent: GateRule = { signal, context, _, _ ->
    if (dedupeKey(signal, context.now) in context.sent) {
        GateResult(Verb.WAIT, ReasonCode.ALREADY_SENT.value, false, false)
    } else {
        null
    }
}

private val quietHours: GateRule = { signal, context, _, _ ->
    if (isQuiet(context.now, context.quietHours) && signal.severity != "critical") {
        GateResult(Verb.WAIT, ReasonCode.QUIET_HOURS.value, true, false)
    } else {
        null
    }
}

private val budget: GateRule = { _, context, _, delivered ->
    val cap = context.signalInterruptionBudget
    if (cap != null && delivered >= cap) {
        GateResult(Verb.WAIT, ReasonCode.BUDGET.value, false, false)
    } else {
        null
    }
}

private val overdueEscalation: GateRule = { signal, context, _, _ ->
    val window = context.escalateAfterHours
    when {
        window == null || signal.severity != "critical" -> null
        else -> {
            val hours = hoursUntil(context.now, signal.due)
            if (hours != null && -hours > window) {
                GateResult(Verb.ESCALATE, ReasonCode.OVERDUE_ESCALATION.value, true, true)
            } else {
                // Critical with an escalation window but not overdue stays a guide;
                // it must not fall through to the act gate.
                GateResult(Verb.GUIDE, ReasonCode.WORTH_SURFACING.value, true, true)
            }
        }
    }
}

private val act: GateRule = { signal, context, _, _ ->
    if (context.allowAct && signal.intent != null && signal.reversible) {
        GateResult(Verb.ACT, ReasonCode.ACT.value, true, true)
    } else {
        null
    }
}

/** The first gate that fires decides. Change this list to change behaviour. */
val GATE_RULES: List<Pair<Gate, GateRule>> =
    listOf(
        Gate.KILL_SWITCH to killSwitch,
        Gate.MUTED to muted,
        Gate.FEEDBACK to feedback,
        Gate.LOW_CONFIDENCE to lowConfidence,
        Gate.BELOW_FLOOR to belowFloor,
        Gate.ALREADY_SENT to alreadySent,
        Gate.QUIET_HOURS to quietHours,
        Gate.BUDGET to budget,
        Gate.OVERDUE_ESCALATION to overdueEscalation,
        Gate.ACT to act,
    )

val GATES: List<String> = GATE_RULES.map { it.first.value }
