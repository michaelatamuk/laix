package dev.laix.decision.policies.packs

import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.utcNow
import java.time.Duration

/** Turn open commitments into the next task move. */
class PlanningPolicy(
    val ledger: CommitmentLedger,
    val commitmentGraph: CommitmentGraph? = null,
    val requireVerified: Boolean = false,
    val maxVerificationAge: Duration? = null,
) : DecisionPolicy {
    override val name: String = "planning.v1"
    val version: String = name

    override fun decide(request: DecisionRequest): List<Decision> {
        val now = parseIso(request.at) ?: utcNow()
        val graph = commitmentGraph
        val commitment: dev.laix.decision.commitments.Commitment?
        val blocked: List<dev.laix.decision.commitments.Commitment>
        if (graph != null) {
            commitment = graph.nextActionable(now, requireVerified, maxVerificationAge)
            blocked = graph.blockedOpen(requireVerified, now, maxVerificationAge)
        } else {
            commitment = ledger.nextActionable(now)
            blocked = ledger.blockedOpen()
        }
        if (commitment == null) {
            if (blocked.isNotEmpty()) {
                val first = blocked.first()
                return listOf(
                    decision(
                        verb = Verb.ASK,
                        reasonCode = "blocked_commitment",
                        rationale = "${first.id} waits on another commitment",
                        confidence = 0.7,
                        actionId = first.id,
                        attributes = mapOf("commitment_id" to first.id),
                    ),
                )
            }
            return listOf(
                decision(Verb.WAIT, "no_commitment", "there is no open commitment", 0.8),
            )
        }
        if (commitment.isDue(now)) {
            return listOf(
                decision(
                    Verb.ACT,
                    "due_commitment",
                    "${commitment.id} is due",
                    0.9,
                    actionId = commitment.id,
                ),
            )
        }
        return listOf(
            decision(
                Verb.WAIT,
                "not_due",
                "${commitment.id} is not due yet",
                0.8,
                actionId = commitment.id,
            ),
        )
    }

    private fun decision(
        verb: Verb,
        reasonCode: String,
        rationale: String,
        confidence: Double,
        actionId: String? = null,
        attributes: Map<String, Any?> = emptyMap(),
    ): Decision =
        Decision(
            verb = verb,
            confidence = confidence,
            reasonCode = reasonCode,
            rationale = rationale,
            actionId = actionId,
            attributes = attributes,
            policyVersion = name,
        )
}
