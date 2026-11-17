package dev.laix.examples.decision.explain

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.explain.CounterfactualVariable
import dev.laix.decision.planners.explain.counterfactualAttribution
import dev.laix.decision.planners.explain.counterfactualSearch
import dev.laix.decision.planners.explain.decisionCounterfactual
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.examples.AT
import dev.laix.examples.sinkOptions

/** The smallest single-component change that would flip a linear decision. */
fun counterfactualAttribution(): String {
    val decision = Decision(
        verb = Verb.ACT,
        confidence = 0.8,
        reasonCode = "live_decision",
        rationale = "chosen has the best total",
        actionId = "chosen",
        score = 0.8,
        attributes = mapOf("utility" to 0.8),
        alternatives = listOf(
            mapOf("action_id" to "other", "total" to 0.5, "utility" to 0.5),
        ),
    )
    val report = counterfactualAttribution(decision)
    val minimal = report.minimal ?: return "no counterfactual"
    return "alternative=${minimal.alternativeId} component=${minimal.component} " +
        "delta=${minimal.delta} resulting=${minimal.resultingTotal}"
}

/** Search bounded numeric inputs for the smallest change that flips a decision. */
fun counterfactualSearchExample(): String {
    val result = counterfactualSearch(
        decide = { values -> if ((values["risk"] ?: 0.0) >= 0.6) "escalate" else "act" },
        variables = listOf(
            CounterfactualVariable(name = "risk", value = 0.2, lower = 0.0, upper = 1.0, step = 0.1),
        ),
        maxChanges = 1,
    )
    val change = result.changes.singleOrNull()
    return "flips=${result.counterfactualId} delta=${change?.delta} evaluations=${result.evaluations}"
}

/** Ask what a candidate problem would decide, and whether it flips the base action. */
fun decisionCounterfactual(): String {
    val problem = PlannerInput(subject = "pick", at = AT, options = sinkOptions())
    val cheaper = problem.copy(
        options = listOf(
            ActionOption("wait", Verb.WAIT, "keep watching", expectedBenefit = 0.9),
            ActionOption("act", Verb.ACT, "close the valve", expectedBenefit = 0.1),
        ),
    )
    val result = decisionCounterfactual(
        problem = problem,
        planner = UtilityPlanner(),
        candidates = mapOf("raise the wait benefit" to cheaper),
    )
    return "base=${result.baseActionId} flips=${result.flips.map { it.name }}"
}
