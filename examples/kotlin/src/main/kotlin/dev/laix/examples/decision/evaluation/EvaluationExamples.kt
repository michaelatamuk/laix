package dev.laix.examples.decision.evaluation

import dev.laix.decision.appkit.bench.FixedActionPlanner
import dev.laix.decision.appkit.bench.runBench
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.evaluation.bench.runLiveBench
import dev.laix.decision.evaluation.cases.Case
import dev.laix.decision.evaluation.cases.compare
import dev.laix.decision.evaluation.simulation.Scenario
import dev.laix.decision.evaluation.simulation.Simulator
import dev.laix.decision.evaluation.simulation.comparePlanners
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import dev.laix.decision.planners.mdp.MDPPlanner
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.examples.AT

/** Replay labelled cases against a policy and report agreement. */
fun evaluationCases(): String {
    val policy = RulePolicy(
        rules = listOf(
            Rule(
                condition = mapOf("risk" to mapOf("gte" to 0.8)),
                verb = Verb.ESCALATE,
                reasonCode = "high_risk",
            ),
        ),
        fallback = Rule(condition = emptyMap(), verb = Verb.WAIT, reasonCode = "no_rule"),
    )
    val cases = listOf(
        Case(
            id = "high-risk",
            request = DecisionRequest(
                subject = "review",
                at = AT,
                attributes = mapOf("risk" to 0.9),
            ),
            expected = listOf(mapOf("verb" to "escalate", "reason_code" to "high_risk")),
        ),
        Case(
            id = "low-risk",
            request = DecisionRequest(
                subject = "review",
                at = AT,
                attributes = mapOf("risk" to 0.1),
            ),
            expected = listOf(mapOf("verb" to "wait", "reason_code" to "no_rule")),
        ),
    )
    val report = compare(cases, decide = { request -> policy.decide(request as DecisionRequest) })
    return "${report.passed}/${report.total} agreement=${report.agreementRate}"
}

/** Run the packaged decision-class bench for one suite. */
fun decisionBench(): String {
    val report = runBench(listOf("safety"))
    return "total=${report.total} passed=${report.passed} agreement=${report.agreement}"
}

/** Compare a planner with a do-nothing baseline on a chain scenario. */
fun plannerSimulation(): String {
    val model = MdpModel(
        states = listOf("s0", "s1", "s2"),
        actions = listOf("go", "stay"),
        transitions = listOf(
            MdpTransition("s0", "go", "s1", 1.0, 1.0),
            MdpTransition("s1", "go", "s2", 1.0, 1.0),
            MdpTransition("s0", "stay", "s0", 1.0, 0.0),
            MdpTransition("s1", "stay", "s1", 1.0, 0.0),
            MdpTransition("s2", "stay", "s2", 1.0, 0.0),
        ),
        start = "s0",
        horizon = 2,
    )
    val report = comparePlanners(
        planners = mapOf(
            "mdp" to MDPPlanner(model),
            "stay" to FixedActionPlanner("stay"),
        ),
        scenarios = listOf(
            Scenario(name = "chain", simulator = Simulator.fromMdp(model), optimum = 2.0),
        ),
    )
    return "best=${report.best()} mdp=${report.summary()["mdp"]?.get("mean_reward")}"
}

/** Run the live bench and print the planner metrics header. */
fun liveBench(): String {
    val report = runLiveBench()
    val firstMetric = report.metrics.minByOrNull { it.planner } ?: return "no metrics"
    return "cases=${report.cases.size} planners=${report.planners.size} " +
        "accuracy(${firstMetric.planner})=${firstMetric.accuracy}"
}
