package dev.laix.decision.planners.commitment

import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentRef
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.time.Duration
import java.time.OffsetDateTime
import java.util.Locale

/**
 * Weight an option by the chance its external dependencies complete.
 *
 * Completion probabilities come from `attributes["commitment_probabilities"]`
 * (keyed by `owner/ledger/id`, `owner:id` or plain id), then from the
 * commitment's `payload["completion_probability"]`, then from
 * `default_probability`. Trusted and verified promises count as certain.
 */
class CommitmentBeliefPlanner(
    private val model: UtilityModel = UtilityModel(),
    val defaultProbability: Double = 0.5,
    val verifyBelow: Double = 0.7,
    val requireVerified: Boolean = true,
    val maxVerificationAge: Duration? = null,
) : Planner {
    init {
        require(defaultProbability in 0.0..1.0) {
            "default_probability must be between zero and one"
        }
        require(verifyBelow in 0.0..1.0) { "verify_below must be between zero and one" }
    }

    val name: String = "commitment_belief.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model)
        val (active, graph) = activeAndGraph(problem)
        val attributes = problem.attributes
        val now = plannerNow(problem)
        val rows = options.map { option ->
            val utility = activeModel.score(option)
            val effect = commitmentEffect(option)
            val refs = effect.fulfills
                .mapNotNull { active[it] }
                .flatMap { graph.dependencies(it) }
                .distinct()
            val probability = if (refs.isNotEmpty()) {
                refs.minOf { probability(it, graph, attributes, now) }
            } else {
                1.0
            }
            Row(
                option = option,
                utility = round6(utility),
                probability = round6(probability),
                expected = round6(utility * probability),
                refs = refs,
                feasible = activeModel.feasible(option),
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            return wait("no_feasible_option", "every option breaks a hard limit")
        }

        val ranked = feasible.sortedWith(compareBy({ -it.expected }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.expected

        if (best.probability < verifyBelow && best.refs.isNotEmpty()) {
            val refs = best.refs.map {
                linkedMapOf(
                    "owner" to it.owner,
                    "ledger" to it.ledger,
                    "id" to it.id,
                    "reason" to "uncertain",
                )
            }
            return PlannerResult(
                verb = Verb.VERIFY,
                confidence = clamp(1.0 - best.probability),
                reasonCode = "commitment_belief_verify",
                rationale = format(
                    "%s depends on a promise with completion probability %.3f",
                    best.option.id,
                    best.probability,
                ),
                actionId = "resolve-commitments",
                intent = Intent("verify_commitment", mapOf("refs" to refs)),
                reversible = true,
                attributes = linkedMapOf(
                    "completion_probability" to best.probability,
                    "verification_refs" to refs,
                ),
            )
        }

        val alternatives = rows
            .filter { it.option.id != best.option.id }
            .map { row ->
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.utility,
                    "completion_probability" to row.probability,
                    "expected_utility" to row.expected,
                    "rejected_reason_code" to if (row.feasible) {
                        "lower_expected_utility"
                    } else {
                        "outside_hard_limits"
                    },
                )
            }

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.expected, second),
            reasonCode = "commitment_belief",
            rationale = format(
                "%s has expected utility %.3f at completion probability %.3f",
                best.option.id,
                best.expected,
                best.probability,
            ),
            actionId = best.option.id,
            requiresApproval = best.option.requiresApproval,
            reversible = best.option.reversible,
            score = best.expected,
            alternatives = alternatives,
            attributes = linkedMapOf(
                "utility" to best.utility,
                "completion_probability" to best.probability,
                "expected_utility" to best.expected,
            ),
        )
    }

    private fun probability(
        ref: CommitmentRef,
        graph: CommitmentGraph,
        attributes: Map<String, Any?>,
        now: OffsetDateTime,
    ): Double {
        val item = graph.get(ref) ?: return 0.0
        val trusted = item.status == "done" &&
            item.trusted &&
            (maxVerificationAge == null || graph.isFresh(item, now, maxVerificationAge))
        if (trusted) return 1.0

        val explicit = attributes["commitment_probabilities"]
        if (explicit is Map<*, *>) {
            for (key in listOf(
                "${ref.owner}/${ref.ledger ?: ""}/${ref.id}",
                "${ref.owner}:${ref.id}",
                ref.id,
            )) {
                if (explicit.containsKey(key)) {
                    val value = explicit[key]
                    val numeric = when (value) {
                        is Number -> value.toDouble()
                        is String -> value.toDoubleOrNull()
                        else -> null
                    }
                    if (numeric != null) return clamp(numeric)
                }
            }
        }

        val payloadValue = item.payload["completion_probability"]
        if (payloadValue != null) {
            val numeric = when (payloadValue) {
                is Number -> payloadValue.toDouble()
                is String -> payloadValue.toDoubleOrNull()
                else -> null
            }
            if (numeric != null) return clamp(numeric)
        }
        return defaultProbability
    }

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }

    private fun wait(reasonCode: String, rationale: String): PlannerResult =
        PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = reasonCode,
            rationale = rationale,
            score = 0.0,
        )

    private fun format(pattern: String, vararg args: Any): String =
        String.format(Locale.ROOT, pattern, *args)

    private data class Row(
        val option: dev.laix.decision.contracts.ActionOption,
        val utility: Double,
        val probability: Double,
        val expected: Double,
        val refs: List<CommitmentRef>,
        val feasible: Boolean,
    )
}
