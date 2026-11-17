package dev.laix.decision.planners.explain

import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.signals.parseIso
import java.time.OffsetDateTime

/** The decision under one counterfactual input. */
data class CounterfactualOutcome(
    val name: String,
    val baseActionId: String?,
    val counterfactualActionId: String?,
    val changed: Boolean,
)

/** The base action and the counterfactual outcomes that flip it. */
data class DecisionCounterfactualResult(
    val baseActionId: String?,
    val outcomes: List<CounterfactualOutcome>,
) {
    val flips: List<CounterfactualOutcome>
        get() = outcomes.filter { it.changed }
}

/** Solve the base problem and each named counterfactual. */
fun decisionCounterfactual(
    problem: PlannerInput,
    planner: Planner,
    candidates: Map<String, PlannerInput>,
): DecisionCounterfactualResult {
    val base = planner.solve(problem)
    val outcomes = candidates.map { (name, candidate) ->
        val result = planner.solve(candidate)
        CounterfactualOutcome(
            name = name,
            baseActionId = base.actionId,
            counterfactualActionId = result.actionId,
            changed = result.actionId != base.actionId,
        )
    }
    return DecisionCounterfactualResult(base.actionId, outcomes)
}

/** Show which external verification would change the decision. */
fun commitmentVerificationCounterfactual(
    problem: PlannerInput,
    planner: Planner,
    now: OffsetDateTime? = null,
): DecisionCounterfactualResult {
    val attributes = problem.attributes
    val graph = attributes["commitment_graph"] as? CommitmentGraph
        ?: return decisionCounterfactual(problem, planner, emptyMap())
    val timestamp = (now ?: parseIso(problem.at)
        ?: throw IllegalArgumentException("problem.at is not parseable")).toString()
    val candidates = LinkedHashMap<String, PlannerInput>()
    for (item in graph.external) {
        if (item.trusted) continue
        val replacement = item.copy(source = "verified", verifiedAt = timestamp)
        val external = graph.external.map { other ->
            if (other.key == item.key) replacement else other
        }
        val candidateGraph = CommitmentGraph(graph.local, external)
        candidates["${item.owner}/${item.id}"] = problem.copy(
            attributes = attributes + mapOf("commitment_graph" to candidateGraph),
        )
    }
    return decisionCounterfactual(problem, planner, candidates)
}
