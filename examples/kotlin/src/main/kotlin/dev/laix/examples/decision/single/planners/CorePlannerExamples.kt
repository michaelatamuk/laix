package dev.laix.examples.decision.single.planners

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Verb
import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.planners.attention.HumanAttentionPlanner
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.composite.LiveCompositePlanner
import dev.laix.decision.planners.execution.ExecutionRiskPlanner
import dev.laix.decision.planners.utility.RiskAttitude
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.examples.AT
import dev.laix.examples.paymentOptions
import dev.laix.examples.sinkOptions
import dev.laix.examples.sinkSituation

/** Score the offered options and pick the highest expected utility. */
fun utilityPlanner(): String {
    val planner = UtilityPlanner(
        UtilityModel(riskAttitude = RiskAttitude.AVERSE, maxRisk = 0.5),
    )
    val result = planner.solve(
        PlannerInput(
            subject = "kitchen sink",
            at = AT,
            situation = sinkSituation(),
            options = sinkOptions(),
        ),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId} score=${result.score}"
}

/** Keep an open promise: the option that fulfils it wins. */
fun commitmentPlanner(): String {
    val commitments = CommitmentLedger(
        listOf(
            Commitment(id = "report", subject = "send the report", due = "2026-11-01T09:00:00+00:00"),
        ),
    )
    val options = listOf(
        ActionOption(
            "delay",
            Verb.WAIT,
            "wait",
            expectedBenefit = 0.2,
            params = mapOf("commitments" to mapOf("violates" to listOf("report"))),
        ),
        ActionOption(
            "send",
            Verb.ACT,
            "send_report",
            expectedBenefit = 0.7,
            params = mapOf("commitments" to mapOf("fulfills" to listOf("report"))),
        ),
    )
    val result = CommitmentPlanner().solve(
        PlannerInput(
            subject = "keep the promise",
            at = AT,
            options = options,
            attributes = mapOf("commitments" to commitments),
        ),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId}"
}

/** Prefer the reversible action when an irreversible one is risky. */
fun executionRiskPlanner(): String {
    val options = listOf(
        ActionOption(
            "drop-table",
            Verb.ACT,
            "drop_table",
            expectedBenefit = 0.9,
            reversible = false,
            params = mapOf("unknown_risk" to 0.9),
        ),
        ActionOption(
            "archive",
            Verb.ACT,
            "archive_table",
            expectedBenefit = 0.7,
            reversible = true,
            params = mapOf("unknown_risk" to 0.1),
        ),
    )
    val result = ExecutionRiskPlanner().solve(
        PlannerInput(subject = "cleanup", at = AT, options = options),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId}"
}

/** Spend the last of a person's attention budget on the option that needs it least. */
fun humanAttentionPlanner(): String {
    val options = listOf(
        ActionOption(
            "interrupt-now",
            Verb.ASK,
            "call_the_owner",
            expectedBenefit = 0.9,
            interruptCost = 0.9,
        ),
        ActionOption(
            "digest",
            Verb.GUIDE,
            "add_to_digest",
            expectedBenefit = 0.6,
            interruptCost = 0.1,
        ),
    )
    val result = HumanAttentionPlanner().solve(
        PlannerInput(
            subject = "notify",
            at = AT,
            options = options,
            attributes = mapOf("human_attention_budget" to mapOf("total" to 1.0, "spent" to 0.4)),
        ),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId}"
}

/** One planner result that keeps the promise, stays reversible and respects attention. */
fun liveCompositePlanner(): String {
    val commitments = CommitmentLedger(
        listOf(Commitment(id = "report", subject = "send the report")),
    )
    val options = listOf(
        ActionOption(
            "risky",
            Verb.ACT,
            "publish_now",
            expectedBenefit = 0.95,
            interruptCost = 0.8,
            params = mapOf("commitments" to mapOf("violates" to listOf("report"))),
        ),
        ActionOption(
            "safe",
            Verb.ACT,
            "review_then_publish",
            expectedBenefit = 0.7,
            interruptCost = 0.1,
            params = mapOf("commitments" to mapOf("fulfills" to listOf("report"))),
        ),
    )
    val result = LiveCompositePlanner().solve(
        PlannerInput(
            subject = "publish",
            at = AT,
            options = options,
            attributes = mapOf(
                "commitments" to commitments,
                "human_attention_budget" to mapOf("total" to 1.0, "spent" to 0.2),
            ),
        ),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId} " +
        "commitment=${result.attributes["commitment_score"]}"
}

/** A hard latency constraint removes the slow option. */
fun hardConstraint(): String {
    val situation = sinkSituation().copy(
        constraints = listOf(Constraint("latency", "latency", 200, hard = true)),
    )
    val options = sinkOptions() + ActionOption(
        "slow",
        Verb.ACT,
        "wait_for_approval",
        expectedBenefit = 0.99,
        latencyMs = 5_000,
    )
    val result = UtilityPlanner().solve(
        PlannerInput(subject = "kitchen sink", at = AT, situation = situation, options = options),
    )
    return "${result.verb.value} ${result.reasonCode} ${result.actionId}"
}

/** A payment that needs approval: the decision carries the flag, not the execution. */
fun approvalDecision(): String {
    val result = UtilityPlanner().solve(
        PlannerInput(
            subject = "electricity bill",
            at = AT,
            situation = dev.laix.examples.paymentSituation(),
            options = paymentOptions(),
        ),
    )
    return "${result.verb.value} ${result.actionId} approval=${result.requiresApproval}"
}
