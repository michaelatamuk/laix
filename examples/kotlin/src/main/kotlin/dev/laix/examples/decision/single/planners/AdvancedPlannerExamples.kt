package dev.laix.examples.decision.single.planners

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.casebased.CaseBasedPlanner
import dev.laix.decision.planners.casebased.PastDecision
import dev.laix.decision.planners.conflict.ConflictResolutionPlanner
import dev.laix.decision.planners.decisionvalue.CAVODPlanner
import dev.laix.decision.planners.mdp.MDPPlanner
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.planners.pomdp.ObservationProbability
import dev.laix.decision.planners.pomdp.POMDPPlanner
import dev.laix.decision.planners.pomdp.PomdpModel
import dev.laix.decision.planners.pomdp.PomdpTransition
import dev.laix.decision.planners.portfolio.PortfolioPlanner
import dev.laix.decision.planners.risk.RiskBoundedPlanner
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.examples.AT
import dev.laix.examples.sinkOptions

private fun chainModel(horizon: Int = 3): MdpModel {
    val states = (0..horizon).map { "s$it" }
    val transitions = (0 until horizon).flatMap { index ->
        listOf(
            MdpTransition("s$index", "go", "s${index + 1}", 1.0, 1.0),
            MdpTransition("s$index", "stay", "s$index", 1.0, 0.0),
        )
    }
    return MdpModel(
        states = states,
        actions = listOf("go", "stay"),
        transitions = transitions,
        start = "s0",
        horizon = horizon,
    )
}

/** A finite MDP: walk a forward chain toward the reward. */
fun mdpPlanner(): String {
    val plan = MDPPlanner(chainModel()).solve(
        PlannerInput(subject = "chain", at = AT, attributes = mapOf("state" to "s0")),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}

/** A POMDP: decide under uncertainty about the current state. */
fun pomdpPlanner(): String {
    val model = PomdpModel(
        states = listOf("dry", "wet"),
        actions = listOf("check", "ignore"),
        observations = listOf("dry", "wet"),
        transitions = listOf(
            PomdpTransition("dry", "check", "dry", 1.0, 0.0),
            PomdpTransition("wet", "check", "wet", 1.0, 0.0),
            PomdpTransition("dry", "ignore", "dry", 1.0, -0.1),
            PomdpTransition("wet", "ignore", "wet", 1.0, -1.0),
        ),
        observationTable = listOf(
            ObservationProbability("dry", "check", "dry", 0.95),
            ObservationProbability("dry", "check", "wet", 0.05),
            ObservationProbability("wet", "check", "wet", 0.95),
            ObservationProbability("wet", "check", "dry", 0.05),
            ObservationProbability("dry", "ignore", "dry", 1.0),
            ObservationProbability("wet", "ignore", "wet", 1.0),
        ),
        horizon = 2,
    )
    val plan = POMDPPlanner(model, belief = mapOf("dry" to 0.6, "wet" to 0.4)).solve(
        PlannerInput(subject = "sink sensor", at = AT),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}

/** Value of deciding later: information has a price and a payoff. */
fun cavodPlanner(): String {
    val options = listOf(
        ActionOption(
            "check",
            Verb.OBSERVE,
            "read_the_meter",
            expectedBenefit = 0.3,
            cost = 0.1,
            params = mapOf(
                "information_gain" to 0.8,
                "option_value" to 0.6,
            ),
        ),
        ActionOption("act", Verb.ACT, "shut_the_valve", expectedBenefit = 0.8),
    )
    val plan = CAVODPlanner().solve(
        PlannerInput(
            subject = "sink",
            at = AT,
            options = options,
            attributes = mapOf("uncertainty" to 0.8),
        ),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}

/** Route to the planner that fits the request shape. */
fun portfolioPlanner(): String {
    val portfolio = PortfolioPlanner(
        planners = mapOf(
            "utility" to UtilityPlanner(),
            "risk" to RiskBoundedPlanner(maxLoss = 0.2),
        ),
        default = "utility",
    )
    val plan = portfolio.solve(
        PlannerInput(subject = "pick", at = AT, options = sinkOptions()),
    )
    return "${plan.verb.value} ${plan.actionId} planner=${plan.attributes["planner"]}"
}

/** Reuse a past decision when the subject looks the same. */
fun caseBasedPlanner(): String {
    val planner = CaseBasedPlanner(
        cases = listOf(PastDecision("late parcel", "check-tracking")),
        fallback = UtilityPlanner(),
    )
    val options = listOf(
        ActionOption("check-tracking", Verb.OBSERVE, "read_the_tracking_page", expectedBenefit = 0.8),
        ActionOption("wait", Verb.WAIT, "keep_waiting", expectedBenefit = 0.1),
    )
    val plan = planner.solve(
        PlannerInput(subject = "late parcel", at = AT, options = options),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}

/** A worst-case loss limit rejects the high-variance option. */
fun riskBoundedPlanner(): String {
    val options = listOf(
        ActionOption(
            "bet",
            Verb.ACT,
            "take_the_bet",
            expectedBenefit = 0.9,
            params = mapOf("worst_case_loss" to 0.8, "cvar_loss" to 0.6),
        ),
        ActionOption(
            "hedge",
            Verb.ACT,
            "hedge",
            expectedBenefit = 0.6,
            params = mapOf("worst_case_loss" to 0.1, "cvar_loss" to 0.05),
        ),
    )
    val plan = RiskBoundedPlanner(maxLoss = 0.3).solve(
        PlannerInput(subject = "invest", at = AT, options = options),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}

/** Two goals disagree; one option resolves both. */
fun conflictResolution(): String {
    val conflicts = listOf(
        mapOf("id" to "speed-vs-safety", "severity" to 0.7),
        mapOf("id" to "cost-vs-quality", "severity" to 0.6),
    )
    val options = listOf(
        ActionOption(
            "resolve",
            Verb.ACT,
            "review_then_ship",
            expectedBenefit = 0.8,
            params = mapOf("resolves" to listOf("speed-vs-safety", "cost-vs-quality")),
        ),
        ActionOption("ship", Verb.ACT, "ship_now", expectedBenefit = 0.6),
    )
    val plan = ConflictResolutionPlanner(planner = UtilityPlanner()).solve(
        PlannerInput(
            subject = "release",
            at = AT,
            options = options,
            attributes = mapOf("goal_conflicts" to conflicts),
        ),
    )
    return "${plan.verb.value} ${plan.reasonCode} ${plan.actionId}"
}
