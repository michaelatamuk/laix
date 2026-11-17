package dev.laix.decision.policies.packs

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.pythonEquals
import dev.laix.decision.support.pythonIn

/** One condition and the decision it produces. */
data class Rule(
    val condition: Map<String, Any?>,
    val verb: Verb,
    val reasonCode: String,
    val rationale: String = "",
    val confidence: Double = 0.8,
    val actionId: String? = null,
    val requiresApproval: Boolean = false,
    val intent: Intent? = null,
)

/** A deterministic policy authored as a list of [Rule] objects. */
class RulePolicy(
    rules: List<Rule>,
    override val name: String = "rules.v1",
    fallback: Rule? = null,
) : DecisionPolicy {
    val rules: List<Rule> = rules.toList()
    override val version: String = name
    private val fallback: Rule = fallback ?: Rule(
        condition = emptyMap(),
        verb = Verb.WAIT,
        reasonCode = "no_rule",
        rationale = "no rule matched",
        confidence = 0.5,
    )

    override fun decide(request: DecisionRequest): List<Decision> {
        val attributes = request.attributes
        for (rule in rules) {
            if (matches(attributes, rule.condition)) return listOf(decision(rule))
        }
        return listOf(decision(fallback))
    }

    private fun decision(rule: Rule): Decision =
        Decision(
            verb = rule.verb,
            confidence = rule.confidence,
            reasonCode = rule.reasonCode,
            rationale = rule.rationale.ifEmpty { rule.reasonCode },
            actionId = rule.actionId,
            intent = rule.intent,
            requiresApproval = rule.requiresApproval,
            policyVersion = name,
        )

    private fun matches(attributes: Map<String, Any?>, condition: Map<String, Any?>): Boolean {
        for ((key, expected) in condition) {
            val actual = attributes[key]
            if (expected is Map<*, *>) {
                for ((operator, value) in expected) {
                    val ok = when (operator.toString()) {
                        "gte" -> number(actual)?.let { number(value)?.let { limit -> it >= limit } } ?: false
                        "lte" -> number(actual)?.let { number(value)?.let { limit -> it <= limit } } ?: false
                        "in" -> pythonIn(value, actual)
                        "contains" -> pythonIn(actual, value)
                        else -> false
                    }
                    if (!ok) return false
                }
            } else if (!pythonEquals(actual, expected)) {
                return false
            }
        }
        return true
    }

    private fun number(value: Any?): Double? =
        when (value) {
            is Number -> value.toDouble()
            is String -> value.toDoubleOrNull()
            else -> null
        }
}
