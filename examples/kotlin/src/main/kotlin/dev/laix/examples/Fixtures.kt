package dev.laix.examples

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.signals.QuietHours
import dev.laix.decision.signals.Signal
import dev.laix.decision.signals.SignalContext
import dev.laix.decision.support.round
import java.time.OffsetDateTime

/** The event time every example shares, so output is deterministic. */
const val AT: String = "2026-11-01T10:00:00+00:00"

fun at(): OffsetDateTime = OffsetDateTime.parse(AT)

/** A leaking sink that deserves attention now. */
fun sinkSituation(): Situation =
    Situation(
        id = "sink-1",
        at = AT,
        subject = "kitchen sink",
        beliefs = listOf(
            Belief(
                id = "overflow",
                proposition = "the sink is about to overflow",
                confidence = 0.95,
                updatedAt = AT,
            ),
        ),
        attributes = mapOf("urgency" to 0.9),
    )

fun sinkOptions(): List<ActionOption> =
    listOf(
        ActionOption("option-wait", Verb.WAIT, "keep watching", expectedBenefit = 0.1),
        ActionOption(
            "option-close-valve",
            Verb.ACT,
            "close the valve",
            expectedBenefit = 0.95,
            risk = 0.05,
            reversible = true,
        ),
    )

/** A bill that needs an owner approval before it is paid. */
fun paymentSituation(): Situation =
    Situation(
        id = "payment-1",
        at = AT,
        subject = "electricity bill",
        beliefs = listOf(
            Belief(
                id = "due",
                proposition = "the bill is due today",
                confidence = 0.9,
                updatedAt = AT,
            ),
        ),
        constraints = listOf(
            Constraint(id = "approval", kind = "approval", value = true),
        ),
        attributes = mapOf("urgency" to 0.9),
    )

fun paymentOptions(): List<ActionOption> =
    listOf(
        ActionOption("option-wait", Verb.WAIT, "pay later", expectedBenefit = 0.1),
        ActionOption(
            "option-pay",
            Verb.ACT,
            "pay the bill",
            expectedBenefit = 0.9,
            requiresApproval = true,
            reversible = false,
        ),
    )

/** One high-severity signal. */
fun billSignal(): Signal =
    Signal(
        id = "signal-1",
        kind = "deadline",
        title = "The electricity bill is due",
        detail = "Pay today to avoid a late fee.",
        severity = "high",
        confidence = 0.9,
        due = "2026-11-01T18:00:00+00:00",
    )

/** An attention context that evaluates `now` in the signal's own time zone. */
fun attentionContext(
    now: OffsetDateTime = at(),
    quietHours: QuietHours? = QuietHours("22:00", "06:00"),
): SignalContext =
    SignalContext(
        now = now,
        quietHours = quietHours,
        mode = "shadow",
        minSeverity = "high",
    )

/** A tiny helper so examples can print a decision consistently. */
fun summarize(decision: dev.laix.decision.contracts.Decision): String =
    "${decision.verb.value} ${decision.reasonCode} ${decision.actionId ?: "-"} " +
        "conf=${round(decision.confidence, 3)}"
