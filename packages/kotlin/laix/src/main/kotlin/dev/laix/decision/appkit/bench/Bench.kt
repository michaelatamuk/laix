package dev.laix.decision.appkit.bench

import dev.laix.decision.appkit.DecisionClient
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.evaluation.simulation.PlannerBenchmarkRow
import dev.laix.decision.evaluation.simulation.Scenario
import dev.laix.decision.evaluation.simulation.SimulationReport
import dev.laix.decision.evaluation.simulation.Simulator
import dev.laix.decision.evaluation.simulation.comparePlanners
import dev.laix.decision.planners.mdp.MDPPlanner
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.policies.ShadowPolicy
import dev.laix.decision.policies.packs.ActivePerceptionPolicy
import dev.laix.decision.policies.packs.AllocationPolicy
import dev.laix.decision.policies.packs.EscalationPolicy
import dev.laix.decision.policies.packs.NegotiationPolicy
import dev.laix.decision.policies.packs.PreferenceElicitationPolicy
import dev.laix.decision.policies.packs.ReplanningPolicy
import dev.laix.decision.policies.packs.SafetyConstrainedPolicy
import dev.laix.decision.policies.packs.VerificationPolicy
import dev.laix.decision.signals.QuietHours
import dev.laix.decision.signals.Signal
import dev.laix.decision.signals.SignalContext
import dev.laix.decision.signals.SignalFeedback
import dev.laix.decision.support.round
import java.time.OffsetDateTime

private const val AT = "2026-11-01T10:00:00+00:00"

/** One deterministic bench case: a request and the fields it should produce. */
data class BenchCase(
    val id: String,
    val request: DecisionRequest,
    val expected: Map<String, Any?>,
)

/** One bench suite: a named decision class and its cases. */
data class Suite(
    val name: String,
    val description: String,
    val policy: () -> dev.laix.decision.contract.DecisionPolicy,
    val cases: List<BenchCase>,
)

/** The compared result of one bench case. */
data class BenchRow(
    val suite: String,
    val case: String,
    val expected: Map<String, Any?>,
    val actual: Map<String, Any?>,
    val mismatches: List<String>,
) {
    val passed: Boolean
        get() = mismatches.isEmpty()
}

val BENCH_FIELDS: List<String> = listOf(
    "verb",
    "reason_code",
    "action_id",
    "requires_approval",
)

/** The report a bench run returns. */
data class BenchReport(
    val rows: List<BenchRow>,
    val fields: List<String> = BENCH_FIELDS,
) {
    val total: Int
        get() = rows.size

    val passed: Int
        get() = rows.count { it.passed }

    val failed: Int
        get() = total - passed

    val agreement: Double
        get() = if (total == 0) 1.0 else round(passed.toDouble() / total, 4)

    fun bySuite(): Map<String, Map<String, Any?>> {
        val names = rows.map { it.suite }.distinct()
        return names.associateWith { name ->
            val subset = rows.filter { it.suite == name }
            val passedCount = subset.count { it.passed }
            linkedMapOf<String, Any?>(
                "cases" to subset.size,
                "passed" to passedCount,
                "failed" to subset.size - passedCount,
                "agreement" to if (subset.isNotEmpty()) {
                    round(passedCount.toDouble() / subset.size, 4)
                } else {
                    1.0
                },
            )
        }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "total" to total,
            "passed" to passed,
            "failed" to failed,
            "agreement" to agreement,
            "fields" to fields,
            "suites" to bySuite(),
            "rows" to rows.map {
                linkedMapOf(
                    "suite" to it.suite,
                    "case" to it.case,
                    "passed" to it.passed,
                    "mismatches" to it.mismatches,
                    "expected" to it.expected,
                    "actual" to it.actual,
                )
            },
        )
}

private fun request(attributes: Map<String, Any?>): DecisionRequest =
    DecisionRequest(subject = "bench case", at = AT, attributes = attributes)

private fun attention(
    signal: Signal,
    now: OffsetDateTime,
    quietHours: QuietHours?,
    feedback: Map<String, SignalFeedback> = emptyMap(),
): DecisionRequest =
    DecisionRequest(
        subject = signal.title.ifEmpty { signal.id },
        at = AT,
        signals = listOf(signal),
        context = SignalContext(now = now, quietHours = quietHours, feedback = feedback),
    )

private fun action(situation: Situation, options: List<ActionOption>): DecisionRequest =
    DecisionRequest(subject = situation.subject, at = AT, situation = situation, options = options)

private fun belief(subject: String) = Belief(
    id = "belief-1",
    proposition = subject,
    confidence = 0.95,
)

private fun billSignal() = Signal(
    id = "bill-1",
    kind = "deadline",
    title = "Electricity bill due tomorrow",
    severity = "high",
    confidence = 0.95,
    due = "2026-11-02T09:00:00+00:00",
)

private fun attentionSuite(): Suite {
    val signal = billSignal()
    val morning = OffsetDateTime.parse("2026-11-01T10:00:00Z")
    val night = OffsetDateTime.parse("2026-11-01T23:30:00Z")
    val quiet = QuietHours("22:00", "06:00")
    return Suite(
        name = "attention",
        description = "which signal deserves attention now",
        policy = { DecisionClient() },
        cases = listOf(
            BenchCase(
                "attention_bill_day",
                attention(signal, morning, quiet),
                mapOf("verb" to "guide", "reason_code" to "worth_surfacing"),
            ),
            BenchCase(
                "signal_attention_quiet_hours",
                attention(signal, night, quiet),
                mapOf("verb" to "wait", "reason_code" to "quiet_hours"),
            ),
            BenchCase(
                "attention_dismissed",
                attention(
                    signal,
                    morning,
                    null,
                    mapOf("bill-1" to SignalFeedback(state = "dismissed")),
                ),
                mapOf("verb" to "wait", "reason_code" to "dismissed"),
            ),
        ),
    )
}

private fun actionSuite(): Suite {
    val sink = Situation(
        id = "sink-1",
        at = AT,
        subject = "kitchen sink",
        beliefs = listOf(belief("the sink is about to overflow")),
        attributes = mapOf("urgency" to 0.9),
    )
    val sinkOptions = listOf(
        ActionOption("option-wait", Verb.WAIT, "keep watching", expectedBenefit = 0.1),
        ActionOption(
            "option-close-valve",
            Verb.ACT,
            "close the valve",
            expectedBenefit = 0.95,
            risk = 0.05,
        ),
    )
    val payment = Situation(
        id = "payment-1",
        at = AT,
        subject = "electricity bill payment",
        beliefs = listOf(belief("the bill is due today")),
        attributes = mapOf("urgency" to 0.9),
    )
    val paymentOptions = listOf(
        ActionOption("option-wait", Verb.WAIT, "pay later", expectedBenefit = 0.1),
        ActionOption(
            "option-pay",
            Verb.ACT,
            "pay the bill",
            expectedBenefit = 0.9,
            requiresApproval = true,
        ),
    )
    val parcel = Situation(
        id = "parcel-1",
        at = AT,
        subject = "late parcel",
        beliefs = listOf(
            Belief(id = "late", proposition = "the parcel is late", confidence = 0.6),
        ),
        attributes = mapOf("urgency" to 0.8, "needs_more_info" to true),
    )
    val parcelOptions = listOf(
        ActionOption("option-wait", Verb.WAIT, "keep waiting", expectedBenefit = 0.2),
        ActionOption(
            "option-check-tracking",
            Verb.OBSERVE,
            "read the tracking page",
            expectedBenefit = 0.6,
        ),
        ActionOption("option-ask-courier", Verb.ASK, "ask the courier", expectedBenefit = 0.4),
    )
    return Suite(
        name = "action",
        description = "which available action to take",
        policy = { DecisionClient() },
        cases = listOf(
            BenchCase(
                "action_sink",
                action(sink, sinkOptions),
                mapOf(
                    "verb" to "act",
                    "reason_code" to "policy_rule",
                    "action_id" to "option-close-valve",
                ),
            ),
            BenchCase(
                "action_payment_approval",
                action(payment, paymentOptions),
                mapOf(
                    "verb" to "act",
                    "reason_code" to "policy_rule",
                    "action_id" to "option-pay",
                    "requires_approval" to true,
                ),
            ),
            BenchCase(
                "action_check_first",
                action(parcel, parcelOptions),
                mapOf(
                    "verb" to "observe",
                    "reason_code" to "policy_rule",
                    "action_id" to "option-check-tracking",
                ),
            ),
        ),
    )
}

private fun activePerceptionSuite() = Suite(
    name = "active-perception",
    description = "look before deciding when uncertainty is high",
    policy = { ActivePerceptionPolicy() },
    cases = listOf(
        BenchCase(
            "active_perception_look",
            request(
                mapOf(
                    "uncertainty" to 0.8,
                    "observations" to listOf(
                        mapOf("id" to "look-1", "information_gain" to 0.7, "cost" to 0.1),
                    ),
                ),
            ),
            mapOf(
                "verb" to "observe",
                "reason_code" to "observe_for_information",
                "action_id" to "look-1",
            ),
        ),
        BenchCase(
            "active_perception_skip",
            request(mapOf("uncertainty" to 0.1)),
            mapOf("verb" to "wait", "reason_code" to "uncertainty_low"),
        ),
    ),
)

private fun safetySuite() = Suite(
    name = "safety",
    description = "act only inside the hard risk limit",
    policy = { SafetyConstrainedPolicy() },
    cases = listOf(
        BenchCase(
            "safety_safe_option",
            request(
                mapOf(
                    "risk_limit" to 0.2,
                    "options" to listOf(
                        mapOf("id" to "valve", "benefit" to 0.9, "risk" to 0.1),
                        mapOf("id" to "hit-pipe", "benefit" to 1.0, "risk" to 0.9),
                    ),
                ),
            ),
            mapOf(
                "verb" to "act",
                "reason_code" to "safe_action",
                "action_id" to "valve",
            ),
        ),
        BenchCase(
            "safety_blocked",
            request(
                mapOf(
                    "risk_limit" to 0.1,
                    "options" to listOf(mapOf("id" to "risky", "benefit" to 1.0, "risk" to 0.9)),
                ),
            ),
            mapOf("verb" to "wait", "reason_code" to "no_safe_option"),
        ),
    ),
)

private fun replanningSuite(): Suite {
    val plans = listOf(
        mapOf("id" to "plan-slow", "success_probability" to 0.95, "cost" to 10, "deadline_risk" to 0.1),
        mapOf("id" to "plan-fast", "success_probability" to 0.8, "cost" to 1, "deadline_risk" to 0.1),
    )
    return Suite(
        name = "replanning",
        description = "choose a replacement plan after the old one broke",
        policy = { ReplanningPolicy() },
        cases = listOf(
            BenchCase(
                "replanning_feasible",
                request(mapOf("plans" to plans, "min_success" to 0.7, "max_cost" to 5)),
                mapOf("verb" to "act", "reason_code" to "replan", "action_id" to "plan-fast"),
            ),
            BenchCase(
                "replanning_none",
                request(mapOf("plans" to plans, "min_success" to 0.99, "max_cost" to 2)),
                mapOf("verb" to "ask", "reason_code" to "no_feasible_plan"),
            ),
        ),
    )
}

private fun allocationSuite(): Suite {
    val requests = listOf(
        mapOf("id" to "a", "value" to 6, "cost" to 4),
        mapOf("id" to "b", "value" to 5, "cost" to 6),
        mapOf("id" to "c", "value" to 9, "cost" to 20),
    )
    return Suite(
        name = "allocation",
        description = "fund a portfolio under a budget",
        policy = { AllocationPolicy() },
        cases = listOf(
            BenchCase(
                "allocation_fund",
                request(mapOf("budget" to 10, "requests" to requests)),
                mapOf("verb" to "act", "reason_code" to "allocate"),
            ),
            BenchCase(
                "allocation_empty",
                request(mapOf("budget" to 1, "requests" to requests)),
                mapOf("verb" to "wait", "reason_code" to "nothing_affordable"),
            ),
        ),
    )
}

private fun negotiationSuite() = Suite(
    name = "negotiation",
    description = "accept, counter or escalate an offer",
    policy = { NegotiationPolicy() },
    cases = listOf(
        BenchCase(
            "negotiation_counter",
            request(mapOf("offer" to 5, "reservation" to 10, "target" to 20, "round" to 1)),
            mapOf("verb" to "act", "reason_code" to "counter_offer", "action_id" to "counter_offer"),
        ),
        BenchCase(
            "negotiation_accept",
            request(mapOf("offer" to 12, "reservation" to 10, "target" to 20, "round" to 1)),
            mapOf("verb" to "act", "reason_code" to "accept_offer", "action_id" to "accept_offer"),
        ),
        BenchCase(
            "negotiation_round_limit",
            request(mapOf("offer" to 5, "reservation" to 10, "target" to 20, "round" to 5)),
            mapOf("verb" to "escalate", "reason_code" to "round_limit"),
        ),
    ),
)

private fun preferenceSuite(): Suite {
    val questions = listOf(
        mapOf("id" to "q1", "information_gain" to 0.2, "cost" to 1),
        mapOf("id" to "q2", "information_gain" to 0.8, "cost" to 1),
    )
    return Suite(
        name = "preference",
        description = "ask the question that reduces preference uncertainty most",
        policy = { PreferenceElicitationPolicy() },
        cases = listOf(
            BenchCase(
                "preference_ask",
                request(mapOf("uncertainty" to 0.8, "questions" to questions)),
                mapOf("verb" to "ask", "reason_code" to "ask_preference", "action_id" to "q2"),
            ),
            BenchCase(
                "preference_known",
                request(mapOf("uncertainty" to 0.1, "questions" to questions)),
                mapOf("verb" to "act", "reason_code" to "preference_known"),
            ),
        ),
    )
}

private fun verificationSuite(): Suite {
    val checks = listOf(
        mapOf("id" to "manual", "confidence_gain" to 0.2, "cost" to 1),
        mapOf("id" to "api", "confidence_gain" to 0.8, "cost" to 1),
    )
    return Suite(
        name = "verification",
        description = "confirm that an action did what it claimed",
        policy = { VerificationPolicy() },
        cases = listOf(
            BenchCase(
                "verification_check",
                request(
                    mapOf(
                        "confidence" to 0.5,
                        "required_confidence" to 0.8,
                        "checks" to checks,
                    ),
                ),
                mapOf("verb" to "verify", "reason_code" to "verify_outcome", "action_id" to "api"),
            ),
            BenchCase(
                "verification_no_path",
                request(
                    mapOf(
                        "confidence" to 0.3,
                        "required_confidence" to 0.8,
                        "checks" to emptyList<Any>(),
                    ),
                ),
                mapOf("verb" to "escalate", "reason_code" to "no_verification_path"),
            ),
            BenchCase(
                "verification_not_needed",
                request(
                    mapOf(
                        "confidence" to 0.95,
                        "required_confidence" to 0.8,
                        "verification_due" to false,
                        "checks" to emptyList<Any>(),
                    ),
                ),
                mapOf("verb" to "wait", "reason_code" to "verification_not_needed"),
            ),
        ),
    )
}

private fun escalationSuite() = Suite(
    name = "escalation",
    description = "decide when a situation must leave the current owner",
    policy = { EscalationPolicy() },
    cases = listOf(
        BenchCase(
            "escalation_target",
            request(mapOf("severity" to 0.9, "severity_threshold" to 0.8, "target" to "manager")),
            mapOf("verb" to "escalate", "reason_code" to "escalate_to_target", "action_id" to "manager"),
        ),
        BenchCase(
            "escalation_within_limits",
            request(mapOf("severity" to 0.2, "severity_threshold" to 0.8, "confidence" to 0.9)),
            mapOf("verb" to "wait", "reason_code" to "within_limits"),
        ),
        BenchCase(
            "escalation_target_required",
            request(mapOf("severity" to 0.9, "severity_threshold" to 0.8)),
            mapOf("verb" to "ask", "reason_code" to "target_required"),
        ),
    ),
)

fun allSuites(): List<Suite> = listOf(
    attentionSuite(),
    actionSuite(),
    activePerceptionSuite(),
    safetySuite(),
    replanningSuite(),
    allocationSuite(),
    negotiationSuite(),
    preferenceSuite(),
    verificationSuite(),
    escalationSuite(),
)

fun suiteNames(): List<String> = allSuites().map { it.name }

/** Run the selected suites and compare each case field by field. */
fun runBench(suites: List<String>? = null): BenchReport {
    val chosen = suites?.toSet() ?: emptySet()
    val selected = allSuites().filter { chosen.isEmpty() || it.name in chosen }
    val rows = mutableListOf<BenchRow>()
    for (suite in selected) {
        val policy = suite.policy()
        for (case in suite.cases) {
            val decisions = policy.decide(case.request)
            val actual = decisions.firstOrNull()?.toMap() ?: emptyMap()
            val mismatches = case.expected.mapNotNull { (name, want) ->
                if (actual[name] != want) "$name: ${actual[name]} != $want" else null
            }
            rows += BenchRow(suite.name, case.id, case.expected, actual, mismatches)
        }
    }
    return BenchReport(rows)
}

/** A baseline that always chooses one action. */
class FixedActionPlanner(private val action: String) : Planner {
    override fun solve(problem: PlannerInput): PlannerResult =
        PlannerResult(
            verb = Verb.ACT,
            confidence = 1.0,
            reasonCode = "fixed_action",
            rationale = "always choose $action",
            actionId = action,
        )
}

private fun chainModel(horizon: Int = 4): MdpModel {
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
        discount = 0.9,
        horizon = horizon,
    )
}

/** Compare the MDP planner with a do-nothing baseline. */
fun runPlannerBench(horizon: Int = 4): SimulationReport {
    val model = chainModel(horizon)
    val scenario = Scenario(
        name = "forward-chain",
        simulator = Simulator.fromMdp(model),
        optimum = horizon.toDouble(),
    )
    return comparePlanners(
        mapOf(
            "mdp" to MDPPlanner(model),
            "stay-baseline" to FixedActionPlanner("stay"),
        ),
        listOf(scenario),
    )
}
