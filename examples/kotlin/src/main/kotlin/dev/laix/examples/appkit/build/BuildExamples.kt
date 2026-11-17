package dev.laix.examples.appkit.build

import dev.laix.decision.appkit.DecisionClient
import dev.laix.decision.appkit.runtime.DecisionRuntime
import dev.laix.decision.appkit.state.ExperienceState
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import dev.laix.examples.AT
import dev.laix.examples.paymentOptions
import dev.laix.examples.paymentSituation
import dev.laix.examples.sinkOptions
import dev.laix.examples.sinkSituation
import dev.laix.examples.summarize

/** The public client: one request in, one decision shape out. */
fun decisionClient(): String {
    val client = DecisionClient()
    val decision = client.decide(
        DecisionRequest(
            subject = "kitchen sink",
            at = AT,
            situation = sinkSituation(),
            options = sinkOptions(),
        ),
    ).single()
    val status = client.status()
    return "${summarize(decision)} policy=${status["policy"]} " +
        "version=${status["policyVersion"]} decisions=${status["decisions"]}"
}

/** Register a custom policy and switch to it at runtime. */
fun policySelection(): String {
    val rules = RulePolicy(
        rules = listOf(
            Rule(
                condition = mapOf("risk" to mapOf("gte" to 0.8)),
                verb = Verb.ESCALATE,
                reasonCode = "high_risk",
            ),
        ),
        fallback = Rule(condition = emptyMap(), verb = Verb.WAIT, reasonCode = "no_rule"),
    )
    val client = DecisionClient(policy = rules)
    val escalated = client.decide(
        DecisionRequest(subject = "review", at = AT, attributes = mapOf("risk" to 0.9)),
    ).single()

    client.registerPolicy(
        "wait",
        RulePolicy(listOf(Rule(condition = emptyMap(), verb = Verb.WAIT, reasonCode = "always_wait"))),
    )
    client.usePolicy("wait")
    val waited = client.decide(
        DecisionRequest(subject = "review", at = AT, attributes = mapOf("risk" to 0.9)),
    ).single()
    return "${escalated.verb.value}/${escalated.reasonCode} -> " +
        "${waited.verb.value}/${waited.reasonCode} policies=${client.policies()}"
}

/** The runtime keeps state, a trace and receipts around the same policy. */
fun decisionRuntime(): String {
    val runtime = DecisionRuntime(state = ExperienceState(subject = "kitchen sink"))
    runtime.observe(
        Observation(
            id = "obs-1",
            at = AT,
            source = "pressure-sensor",
            kind = "pressure",
            confidence = 0.9,
            payload = mapOf(
                "proposition" to "leak",
                "statement" to "the sink is leaking",
                "confidence" to 0.9,
            ),
        ),
    )
    val decision = runtime.decide(
        situation = sinkSituation(),
        options = sinkOptions(),
        attributes = mapOf("urgency" to 0.9),
    )
    val trace = runtime.trace(decision.decisionId)
    return "${summarize(decision)} traceEvents=${trace.events.size} " +
        "beliefs=${runtime.state.beliefs.size} stats=${runtime.stats()["decisions"]}"
}

/** The runtime also executes through the bridge and records receipts. */
fun runtimeExecution(): String {
    val runtime = DecisionRuntime()
    runtime.bridge.register("pay the bill", { _, _ -> mapOf("paid" to true) })
    val decision = runtime.decide(
        situation = paymentSituation(),
        options = paymentOptions(),
        attributes = mapOf("urgency" to 0.9),
    )
    val receipt = runtime.execute(decision, actor = "agent", approver = "lead")
    return "${summarize(decision)} receipt=${receipt.status} receipts=${runtime.receipts().size}"
}

/** A planner behind the policy contract keeps the same decision shape. */
fun plannerAsPolicy(): String {
    val client = DecisionClient(
        policy = dev.laix.decision.contract.PlannerPolicy(dev.laix.decision.planners.utility.UtilityPlanner()),
    )
    val decision = client.decide(
        DecisionRequest(
            subject = "kitchen sink",
            at = AT,
            situation = sinkSituation(),
            options = sinkOptions(),
        ),
    ).single()
    return "${summarize(decision)} version=${client.status()["policyVersion"]}"
}

/** A no-op request to keep the import of PlannerInput honest in this chapter. */
fun plannerInputShape(): String {
    val input = PlannerInput(subject = "kitchen sink", at = AT, options = sinkOptions())
    return "subject=${input.subject} options=${input.options.size}"
}

/** An option can carry an intent the host executes. */
fun optionIntent(): String {
    val option = ActionOption(
        "pay",
        Verb.ACT,
        "pay_bill",
        expectedBenefit = 0.9,
        params = mapOf("invoice" to "4832"),
    )
    return "${option.name} verb=${option.verb.value} params=${option.params}"
}
