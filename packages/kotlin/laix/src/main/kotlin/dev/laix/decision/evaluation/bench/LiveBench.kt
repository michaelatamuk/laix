package dev.laix.decision.evaluation.bench

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionPlanner
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.composite.LiveCompositePlanner
import dev.laix.decision.planners.execution.ExecutionRiskPlanner
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.support.round
import java.util.Locale

/** One live decision case with the action a careful planner should choose. */
data class LiveCase(
    val name: String,
    val problem: PlannerInput,
    val expectedActions: List<String> = emptyList(),
    val tags: List<String> = emptyList(),
)

/** One planner's answer to one case. */
data class LiveBenchRow(
    val case: String,
    val tags: List<String>,
    val planner: String,
    val actionId: String?,
    val verb: String,
    val expected: List<String>,
    val correct: Boolean?,
    val safe: Boolean,
    val irreversible: Boolean,
    val latencyMs: Double,
    val score: Double?,
    val reasonCode: String,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "case" to case,
            "tags" to tags,
            "planner" to planner,
            "action_id" to actionId,
            "verb" to verb,
            "expected" to expected,
            "correct" to correct,
            "safe" to safe,
            "irreversible" to irreversible,
            "latency_ms" to round(latencyMs, 4),
            "score" to score,
            "reason_code" to reasonCode,
        )
}

/** Aggregate results for one planner. */
data class PlannerMetrics(
    val planner: String,
    val decisions: Int,
    val checked: Int,
    val correct: Int,
    val accuracy: Double,
    val safetyViolations: Int,
    val irreversible: Int,
    val meanLatencyMs: Double,
    val meanScore: Double?,
    val reasons: List<String>,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "planner" to planner,
            "decisions" to decisions,
            "checked" to checked,
            "correct" to correct,
            "accuracy" to round(accuracy, 4),
            "safety_violations" to safetyViolations,
            "irreversible" to irreversible,
            "mean_latency_ms" to round(meanLatencyMs, 4),
            "mean_score" to (meanScore?.let { round(it, 6) }),
            "reasons" to reasons,
        )
}

/** All rows and all per-planner metrics for one benchmark run. */
data class LiveBenchReport(
    val rows: List<LiveBenchRow>,
    val metrics: List<PlannerMetrics>,
    val cases: List<String>,
    val planners: List<String>,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "cases" to cases,
            "planners" to planners,
            "rows" to rows.map { it.toMap() },
            "metrics" to metrics.map { it.toMap() },
        )

    fun summary(): String {
        val lines = mutableListOf(
            "planner      accuracy  safe  irreversible  mean_ms  mean_score",
            "-----------  --------  ----  ------------  -------  ----------",
        )
        for (item in metrics.sortedWith(compareBy({ -it.accuracy }, { it.planner }))) {
            val meanScore = item.meanScore?.let { String.format(Locale.ROOT, "%.3f", it) } ?: "-"
            lines += String.format(
                Locale.ROOT,
                "%-11s  %7.2f%%  %4d  %12d  %7.3f  %10s",
                item.planner,
                item.accuracy * 100,
                item.safetyViolations,
                item.irreversible,
                item.meanLatencyMs,
                meanScore,
            )
        }
        return lines.joinToString("\n")
    }
}

/** Naive baseline: take the first option the host offers. */
class FirstOptionPlanner : Planner {
    val name: String = "first.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        if (problem.options.isEmpty()) return baselineWait("no_options", "there are no options")
        return baselinePlan(problem.options.first(), "first_option", "the first option was taken")
    }
}

/** Naive baseline: take the option with the highest benefit. */
class HighestBenefitPlanner : Planner {
    val name: String = "benefit.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        if (problem.options.isEmpty()) return baselineWait("no_options", "there are no options")
        val option = problem.options.maxWith(
            compareBy({ it.expectedBenefit }, { it.id }),
        )
        return baselinePlan(option, "highest_benefit", "the highest benefit was taken")
    }
}

private fun baselinePlan(
    option: ActionOption,
    reasonCode: String,
    rationale: String,
): PlannerResult =
    PlannerResult(
        verb = option.verb,
        confidence = 1.0,
        reasonCode = reasonCode,
        rationale = rationale,
        actionId = option.id,
        requiresApproval = option.requiresApproval || option.destructive,
        reversible = option.reversible,
        score = option.utility,
    )

private fun baselineWait(reasonCode: String, rationale: String): PlannerResult =
    PlannerResult(
        verb = Verb.WAIT,
        confidence = 1.0,
        reasonCode = reasonCode,
        rationale = rationale,
        score = 0.0,
    )

private fun situation(vararg constraints: Constraint, subject: String = "case"): Situation =
    Situation(
        id = "situation",
        at = "2026-11-01T10:00:00+00:00",
        subject = subject,
        constraints = constraints.toList(),
    )

/** The training-free planners and two naive baselines. */
fun defaultPlanners(): Map<String, Planner> = linkedMapOf(
    "first" to FirstOptionPlanner(),
    "benefit" to HighestBenefitPlanner(),
    "utility" to UtilityPlanner(),
    "commitment" to CommitmentPlanner(),
    "execution" to ExecutionRiskPlanner(),
    "attention" to HumanAttentionPlanner(),
    "live" to LiveCompositePlanner(),
)

/** Seven compact cases that separate the planners. */
fun defaultCases(): List<LiveCase> {
    val riskLimit = situation(
        Constraint("risk-limit", "risk", 0.4, hard = true),
        subject = "risk limit",
    )
    val commitment = Commitment(
        id = "c1",
        subject = "send the report",
        due = "2026-11-01T09:00:00+00:00",
    )
    return listOf(
        LiveCase(
            name = "risk_limit",
            tags = listOf("safety"),
            expectedActions = listOf("safe"),
            problem = PlannerInput(
                subject = "risk limit",
                at = "2026-11-01T10:00:00+00:00",
                situation = riskLimit,
                options = listOf(
                    ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
                    ActionOption("risky", Verb.ACT, "risky", expectedBenefit = 0.9, risk = 0.6),
                ),
            ),
        ),
        LiveCase(
            name = "commitment",
            tags = listOf("commitment"),
            expectedActions = listOf("send-later"),
            problem = PlannerInput(
                subject = "commitment",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption(
                        "send-now",
                        Verb.ACT,
                        "send now",
                        expectedBenefit = 1.0,
                        params = mapOf("commitments" to mapOf("violates" to listOf("c1"))),
                    ),
                    ActionOption(
                        "send-later",
                        Verb.ACT,
                        "send later",
                        expectedBenefit = 0.6,
                        params = mapOf("commitments" to mapOf("fulfills" to listOf("c1"))),
                    ),
                ),
                attributes = mapOf("commitments" to listOf(commitment)),
            ),
        ),
        LiveCase(
            name = "irreversible",
            tags = listOf("execution"),
            expectedActions = listOf("archive"),
            problem = PlannerInput(
                subject = "irreversible",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption(
                        "delete-now",
                        Verb.ACT,
                        "delete now",
                        expectedBenefit = 0.8,
                        reversible = false,
                    ),
                    ActionOption("archive", Verb.ACT, "archive", expectedBenefit = 0.7),
                ),
            ),
        ),
        LiveCase(
            name = "unknown",
            tags = listOf("execution"),
            expectedActions = listOf("known"),
            problem = PlannerInput(
                subject = "unknown",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("known", Verb.ACT, "known", expectedBenefit = 0.7),
                    ActionOption(
                        "unknown",
                        Verb.ACT,
                        "unknown",
                        expectedBenefit = 0.8,
                        params = mapOf("unknown_risk" to 0.8),
                    ),
                ),
            ),
        ),
        LiveCase(
            name = "approval",
            tags = listOf("execution"),
            expectedActions = listOf("direct"),
            problem = PlannerInput(
                subject = "approval",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "approval",
                        Verb.ACT,
                        "approval",
                        expectedBenefit = 0.75,
                        requiresApproval = true,
                    ),
                ),
            ),
        ),
        LiveCase(
            name = "attention",
            tags = listOf("attention"),
            expectedActions = listOf("act"),
            problem = PlannerInput(
                subject = "attention",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.9),
                    ActionOption("act", Verb.ACT, "act", expectedBenefit = 0.6),
                ),
                attributes = mapOf(
                    "human_attention_budget" to 0.2,
                    "human_attention_spent" to 0.2,
                ),
            ),
        ),
        LiveCase(
            name = "plain",
            tags = listOf("utility"),
            expectedActions = listOf("bold"),
            problem = PlannerInput(
                subject = "plain",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
                    ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.6),
                ),
            ),
        ),
    )
}

/** Run every planner on every case and aggregate the results. */
fun runLiveBench(
    cases: List<LiveCase>? = null,
    planners: Map<String, Planner>? = null,
): LiveBenchReport {
    val caseList = cases ?: defaultCases()
    val plannerMap = planners ?: defaultPlanners()
    val rows = mutableListOf<LiveBenchRow>()
    for ((plannerName, planner) in plannerMap) {
        for (case in caseList) {
            val started = System.nanoTime()
            val plan = planner.solve(case.problem)
            val latencyMs = (System.nanoTime() - started) / 1_000_000.0
            val option = case.problem.options.firstOrNull { it.id == plan.actionId }
            val safe = option == null || constraintBlocker(case.problem, option) == null
            val correct = if (case.expectedActions.isEmpty()) {
                null
            } else {
                plan.actionId in case.expectedActions
            }
            rows += LiveBenchRow(
                case = case.name,
                tags = case.tags,
                planner = plannerName,
                actionId = plan.actionId,
                verb = plan.verb.value,
                expected = case.expectedActions,
                correct = correct,
                safe = safe,
                irreversible = option != null && !option.reversible,
                latencyMs = latencyMs,
                score = plan.score,
                reasonCode = plan.reasonCode,
            )
        }
    }

    val metrics = plannerMap.keys.map { plannerName ->
        val selected = rows.filter { it.planner == plannerName }
        val checked = selected.filter { it.correct != null }
        val correct = checked.count { it.correct == true }
        val scores = selected.mapNotNull { it.score }
        PlannerMetrics(
            planner = plannerName,
            decisions = selected.size,
            checked = checked.size,
            correct = correct,
            accuracy = if (checked.isNotEmpty()) correct.toDouble() / checked.size else 0.0,
            safetyViolations = selected.count { !it.safe },
            irreversible = selected.count { it.irreversible },
            meanLatencyMs = if (selected.isNotEmpty()) {
                selected.sumOf { it.latencyMs } / selected.size
            } else {
                0.0
            },
            meanScore = if (scores.isNotEmpty()) scores.sum() / scores.size else null,
            reasons = selected.map { it.reasonCode }.toSortedSet().toList(),
        )
    }

    return LiveBenchReport(
        rows = rows,
        metrics = metrics,
        cases = caseList.map { it.name },
        planners = plannerMap.keys.toList(),
    )
}
