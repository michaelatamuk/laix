package dev.laix.examples.decision.domain

import dev.laix.decision.appkit.commitments.InMemoryCommitmentResolver
import dev.laix.decision.appkit.commitments.resolveCommitmentGraph
import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef
import dev.laix.decision.outcomes.OutcomeLedger
import dev.laix.decision.outcomes.attention.SignalAttentionLog
import dev.laix.decision.outcomes.attention.SignalAttentionOutcome
import dev.laix.decision.contracts.Verb
import dev.laix.decision.outcomes.OutcomeLabel
import dev.laix.examples.AT

/** Combine a local promise with one another owner resolved through the host port. */
fun commitmentGraph(): String {
    val supplier = CommitmentRef(owner = "supplier", ledger = "supplier", id = "ship")
    val local = CommitmentLedger(
        listOf(
            Commitment(id = "deliver", subject = "deliver the order", externalDependsOn = listOf(supplier)),
        ),
    )
    val resolver = InMemoryCommitmentResolver(
        listOf(
            Commitment(
                id = "ship",
                subject = "ship the order",
                owner = "supplier",
                ledger = "supplier",
                status = "done",
                source = "verified",
                verifiedAt = AT,
            ),
        ),
    )
    val graph = resolveCommitmentGraph(local, resolver)
    return "commitments=${graph.commitments.size} missing=${graph.missingRefs().size} " +
        "trusted=${graph.get(supplier)?.trusted}"
}

/** Record what changed after a decision and keep it separate from unattributed noise. */
fun outcomeLedger(): String {
    val ledger = OutcomeLedger()
    val helped = ledger.record(
        decisionId = "DEC-1",
        metric = "precision",
        before = 0.5,
        after = 0.8,
        attributed = true,
    )
    val hurt = ledger.record(
        decisionId = "DEC-2",
        metric = "time_to_assessment",
        before = 10.0,
        after = 4.0,
        attributed = true,
        direction = "lower-better",
    )
    val summary = ledger.summary()
    return "labels=${helped.label}/${hurt.label} measured=${summary["measured"]} " +
        "meanGain=${summary["meanGain"]}"
}

/** Score the attention policy on labelled signal outcomes. */
fun signalAttentionOutcomes(): String {
    val log = SignalAttentionLog()
    log.extend(
        listOf(
            SignalAttentionOutcome(
                signalId = "s-1",
                kind = "deadline",
                verb = Verb.GUIDE,
                result = OutcomeLabel.HELPED,
                score = 82.0,
            ),
            SignalAttentionOutcome(
                signalId = "s-2",
                kind = "deadline",
                verb = Verb.GUIDE,
                result = OutcomeLabel.NEUTRAL,
                score = 70.0,
            ),
            SignalAttentionOutcome(
                signalId = "s-3",
                kind = "noise",
                verb = Verb.GUIDE,
                result = OutcomeLabel.HURT,
                score = 60.0,
            ),
        ),
    )
    return "total=${log.total()} precision=${log.precision()} hazard=${log.hazardRate()} " +
        "deadlineAdjustment=${log.adjustment("deadline")}"
}
