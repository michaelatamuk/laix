package dev.laix.decision.planners.commitment

import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import java.time.Duration

/**
 * Resolve blocked hard commitments with a concrete next step.
 *
 * The planner runs the normal commitment planner first. When every option is
 * blocked, it returns `verify` (or `ask` when configured) with the
 * owner-qualified references that must be resolved.
 */
class CommitmentResolutionPlanner(
    model: UtilityModel? = null,
    weights: CommitmentWeights = CommitmentWeights(),
    requireVerified: Boolean = true,
    maxVerificationAge: Duration? = null,
    val mode: String = "verify",
) : Planner {
    init {
        require(mode in listOf("verify", "ask")) {
            "unknown commitment resolution mode: $mode"
        }
    }

    val name: String = "commitment.resolution.v1"

    private val planner = CommitmentPlanner(
        model = model,
        weights = weights,
        requireVerified = requireVerified,
        maxVerificationAge = maxVerificationAge,
    )

    override fun solve(problem: PlannerInput): PlannerResult {
        val base = planner.solve(problem)
        if (base.reasonCode == "no_options" || base.verb != Verb.WAIT) return base

        val (active, graph) = activeAndGraph(problem)
        val now = plannerNow(problem)
        val found = LinkedHashMap<Triple<String, String, String>, Map<String, Any?>>()
        for (option in problem.options) {
            for (blocker in optionBlockers(
                option = option,
                active = active,
                graph = graph,
                requireVerified = planner.requireVerified,
                now = now,
                maxVerificationAge = planner.maxVerificationAge,
            )) {
                found[keyOf(blocker)] = blocker
            }
        }
        if (found.isEmpty()) return base

        val refs = found.keys
            .sortedWith(compareBy({ it.first }, { it.second }, { it.third }))
            .map { found.getValue(it) }
        val verb = if (mode == "ask") Verb.ASK else Verb.VERIFY
        return PlannerResult(
            verb = verb,
            confidence = 0.8,
            reasonCode = "commitment_resolution",
            rationale = "resolve ${refs.size} blocked commitment " +
                (if (refs.size == 1) "dependency" else "dependencies"),
            actionId = "resolve-commitments",
            intent = Intent("verify_commitment", mapOf("refs" to refs)),
            requiresApproval = verb == Verb.ASK,
            reversible = true,
            attributes = linkedMapOf(
                "verification_refs" to refs,
                "blocked_by" to refs,
                "base_reason_code" to base.reasonCode,
            ),
        )
    }

    private fun keyOf(blocker: Map<String, Any?>): Triple<String, String, String> =
        Triple(
            blocker["owner"]?.toString() ?: "",
            blocker["ledger"]?.toString() ?: "",
            blocker["id"]?.toString() ?: "",
        )
}
