package dev.laix.examples.decision.sequence

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.sequence.CABBPlanner
import dev.laix.decision.planners.sequence.DecisionScenario
import dev.laix.decision.planners.sequence.DecisionStep
import dev.laix.decision.planners.sequence.ReplanPlanner
import dev.laix.decision.planners.sequence.RolloutPlanner
import dev.laix.examples.AT

private fun scenario(): DecisionScenario =
    DecisionScenario(
        steps = listOf(
            DecisionStep(
                at = AT,
                options = listOf(
                    ActionOption("send", Verb.ACT, "send_report", expectedBenefit = 0.8),
                    ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.1),
                ),
            ),
            DecisionStep(
                at = "2026-11-01T11:00:00+00:00",
                options = listOf(
                    ActionOption("verify", Verb.VERIFY, "verify_delivery", expectedBenefit = 0.6),
                    ActionOption("stop", Verb.WAIT, "stop", expectedBenefit = 0.1),
                ),
            ),
        ),
    )

/** Plan two steps ahead with bounded search. */
fun cabbPlan(): String {
    val plan = CABBPlanner().plan(scenario())
    return "actions=${plan.actions} score=${plan.score} optimal=${plan.optimal} nodes=${plan.nodes}"
}

/** Roll out the same scenario one option at a time. */
fun rolloutPlan(): String {
    val plan = RolloutPlanner().plan(scenario())
    return "actions=${plan.actions} score=${plan.score} nodes=${plan.nodes}"
}

/** Replan after the first action was already executed. */
fun replan(): String {
    val result = ReplanPlanner().replan(scenario(), executed = listOf("send"))
    return "executed=${result.executed} actions=${result.actions} reason=${result.reason}"
}
