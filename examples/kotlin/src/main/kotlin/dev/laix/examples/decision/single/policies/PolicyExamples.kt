package dev.laix.examples.decision.single.policies

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.packs.ActivePerceptionPolicy
import dev.laix.decision.policies.packs.AllocationPolicy
import dev.laix.decision.policies.packs.BanditPolicy
import dev.laix.decision.policies.packs.EscalationPolicy
import dev.laix.decision.policies.packs.GroupPolicy
import dev.laix.decision.policies.packs.NegotiationPolicy
import dev.laix.decision.policies.packs.PreferenceElicitationPolicy
import dev.laix.decision.policies.packs.ReplanningPolicy
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import dev.laix.decision.policies.packs.SafetyConstrainedPolicy
import dev.laix.decision.policies.packs.TargetedPolicy
import dev.laix.decision.policies.packs.VerificationPolicy
import dev.laix.decision.policies.ShadowPolicy
import dev.laix.decision.contracts.TargetMode
import dev.laix.examples.AT

private fun request(attributes: Map<String, Any?>): DecisionRequest =
    DecisionRequest(subject = "policy", at = AT, attributes = attributes)

private fun summarize(decisions: List<Decision>): String =
    decisions.joinToString(", ") { "${it.verb.value}/${it.reasonCode}/${it.actionId ?: "-"}" }

/** A declarative policy: rules over request attributes, with a fallback. */
fun rulePolicy(): String {
    val policy = RulePolicy(
        rules = listOf(
            Rule(
                condition = mapOf("risk" to mapOf("gte" to 0.8)),
                verb = Verb.ESCALATE,
                reasonCode = "high_risk",
            ),
            Rule(
                condition = mapOf("kind" to "deadline"),
                verb = Verb.GUIDE,
                reasonCode = "remind",
            ),
        ),
        fallback = Rule(condition = emptyMap(), verb = Verb.WAIT, reasonCode = "no_rule"),
    )
    return summarize(policy.decide(request(mapOf("risk" to 0.85))))
}

/** The packaged safety policy drops options above the risk limit. */
fun safetyConstrainedPolicy(): String {
    val policy = SafetyConstrainedPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "risk_limit" to 0.2,
                    "options" to listOf(
                        mapOf("id" to "safe", "risk" to 0.1, "benefit" to 0.6),
                        mapOf("id" to "risky", "risk" to 0.9, "benefit" to 0.9),
                    ),
                ),
            ),
        ),
    )
}

/** The verification policy picks the check that closes the confidence gap. */
fun verificationPolicy(): String {
    val policy = VerificationPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "confidence" to 0.5,
                    "required_confidence" to 0.8,
                    "checks" to listOf(
                        mapOf("id" to "manual", "confidence_gain" to 0.2, "cost" to 1),
                        mapOf("id" to "api", "confidence_gain" to 0.8, "cost" to 1),
                    ),
                ),
            ),
        ),
    )
}

/** Ask the question that reduces preference uncertainty the most. */
fun preferenceElicitation(): String {
    val policy = PreferenceElicitationPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "uncertainty" to 0.8,
                    "questions" to listOf(
                        mapOf("id" to "q1", "information_gain" to 0.2, "cost" to 1),
                        mapOf("id" to "q2", "information_gain" to 0.8, "cost" to 1),
                    ),
                ),
            ),
        ),
    )
}

/** Admit the sensor that buys the most certainty inside the budget. */
fun activePerception(): String {
    val policy = ActivePerceptionPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "uncertainty" to 0.7,
                    "budget" to 2.0,
                    "observations" to listOf(
                        mapOf("id" to "cheap", "information_gain" to 0.2, "cost" to 0.5),
                        mapOf("id" to "deep", "information_gain" to 0.9, "cost" to 1.5),
                    ),
                ),
            ),
        ),
    )
}

/** Replan when the chosen plan no longer clears the bar. */
fun replanningPolicy(): String {
    val policy = ReplanningPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "min_success" to 0.7,
                    "plans" to listOf(
                        mapOf("id" to "slow", "success_probability" to 0.95, "cost" to 10),
                        mapOf("id" to "fast", "success_probability" to 0.6, "cost" to 1),
                    ),
                ),
            ),
        ),
    )
}

/** Escalate past the current owner when severity and limits say so. */
fun escalationPolicy(): String {
    val policy = EscalationPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "severity" to 0.9,
                    "severity_threshold" to 0.8,
                    "target" to "manager",
                ),
            ),
        ),
    )
}

/** A bounded negotiation: counter inside the reservation and target. */
fun negotiationPolicy(): String {
    val policy = NegotiationPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "offer" to 80.0,
                    "reservation" to 100.0,
                    "target" to 140.0,
                    "round" to 1,
                    "max_rounds" to 5,
                ),
            ),
        ),
    )
}

/** Allocate a fixed budget across competing requests. */
fun allocationPolicy(): String {
    val policy = AllocationPolicy()
    return summarize(
        policy.decide(
            request(
                mapOf(
                    "budget" to 10.0,
                    "requests" to listOf(
                        mapOf("id" to "a", "value" to 6, "cost" to 4),
                        mapOf("id" to "b", "value" to 5, "cost" to 6),
                        mapOf("id" to "c", "value" to 9, "cost" to 20),
                    ),
                ),
            ),
        ),
    )
}

/** Learn which arm works: unexplored arms are tried first. */
fun banditPolicy(): String {
    val policy = BanditPolicy()
    val first = policy.decide(
        request(
            mapOf(
                "arms" to listOf(
                    mapOf("id" to "arm-a", "prior_mean" to 0.4),
                    mapOf("id" to "arm-b", "prior_mean" to 0.6),
                ),
            ),
        ),
    )
    policy.record("arm-a", 1.0)
    val second = policy.decide(request(emptyMap()))
    return "${summarize(first)} -> ${summarize(second)}"
}

/** Share a decision with a group and mask the private fields. */
fun groupPolicy(): String {
    val inner: DecisionPolicy = DecisionPolicy {
        listOf(
            Decision(
                verb = Verb.GUIDE,
                confidence = 0.9,
                reasonCode = "share",
                rationale = "share the update",
                attributes = mapOf("topic" to "release", "health" to "private"),
            ),
        )
    }
    val policy = GroupPolicy(
        policy = inner,
        target = "all",
        recipients = listOf("alice", "ben"),
        privateAttributes = listOf("health"),
    )
    val decision = policy.decide(request(emptyMap())).single()
    return "${decision.target.value} ${decision.recipients} ${decision.attributes}"
}

/** Route attention to the team that owns the topic. */
fun targetedPolicy(): String {
    val inner: DecisionPolicy = DecisionPolicy {
        listOf(
            Decision(verb = Verb.GUIDE, confidence = 0.8, reasonCode = "share", rationale = "share"),
        )
    }
    val policy = TargetedPolicy(inner, target = "some", recipients = listOf("ops"))
    val decision = policy.decide(request(emptyMap())).single()
    return "${decision.target.value} ${decision.recipients}"
}

/** Run a shadow policy and compare it with the primary one. */
fun shadowPolicy(): String {
    val primary: DecisionPolicy = DecisionPolicy {
        listOf(Decision(verb = Verb.WAIT, confidence = 0.6, reasonCode = "primary", rationale = "primary"))
    }
    val shadow: DecisionPolicy = DecisionPolicy {
        listOf(Decision(verb = Verb.ACT, confidence = 0.7, reasonCode = "shadow", rationale = "shadow"))
    }
    val policy = ShadowPolicy(primary, shadow)
    policy.decide(request(emptyMap()))
    val difference = policy.differences.single()
    return "primary=${difference.primary.single().verb.value} shadow=${difference.shadow.single().verb.value}"
}
