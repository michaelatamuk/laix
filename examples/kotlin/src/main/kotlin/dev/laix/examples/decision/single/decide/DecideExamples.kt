package dev.laix.examples.decision.single.decide

import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.decide
import dev.laix.examples.AT
import dev.laix.examples.attentionContext
import dev.laix.examples.billSignal
import dev.laix.examples.sinkOptions
import dev.laix.examples.sinkSituation
import dev.laix.examples.summarize

/**
 * Ask the decision layer for one action decision, with no app kit.
 *
 * `decide` selects the action policy from the request shape and returns the same
 * `Decision` shape as the app kit.
 */
fun actionDecide(): String {
    val decision = decide(
        DecisionRequest(
            subject = "kitchen sink",
            at = AT,
            situation = sinkSituation(),
            options = sinkOptions(),
        ),
    ).single()
    return summarize(decision)
}

/** Ask for one attention decision. */
fun attentionDecide(): String {
    val decision = decide(
        DecisionRequest(
            subject = "one decision",
            at = AT,
            signals = listOf(billSignal()),
            context = attentionContext(),
        ),
    ).single()
    return summarize(decision)
}

/** A silent signal: a medium signal below the configured floor. */
fun attentionBelowFloor(): String {
    val quiet = billSignal().copy(id = "signal-2", severity = "medium")
    val decision = decide(
        DecisionRequest(
            subject = "one decision",
            at = AT,
            signals = listOf(quiet),
            context = attentionContext(),
        ),
    ).single()
    return summarize(decision)
}
