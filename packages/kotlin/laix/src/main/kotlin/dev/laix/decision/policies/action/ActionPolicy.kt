package dev.laix.decision.policies.action

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.clamp
import dev.laix.decision.support.iso
import dev.laix.decision.support.round
import dev.laix.decision.support.truthy
import java.util.Locale

const val ACTION_POLICY_VERSION: String = "0.8.0"

/**
 * The built-in action policy: one situation plus its options, one decision.
 *
 * It admits options inside the hard constraints, then walks a fixed verb ladder:
 * escalate on a breach, observe before asking, ask when uncertain, verify an
 * unverified outcome, act when urgency and confidence allow, guide, wait, and
 * finally take the best remaining option.
 */
class ActionPolicy(
    val config: ActionPolicyConfig = ActionPolicyConfig(),
) {
    val version: String = ACTION_POLICY_VERSION

    fun decide(
        request: ActionPolicyInput,
        decisionId: String = "",
        traceId: String = "",
        createdAt: String? = null,
    ): Decision {
        val situation = request.situation
        val attributes = situation.attributes + request.attributes
        val applied = mutableListOf<String>()
        val blocked = linkedMapOf<String, String>()

        val admitted = admit(situation, request.options, applied, blocked)
        val byVerb = Verb.entries.associateWith { verb -> admitted.filter { it.verb == verb } }

        var confidence = situation.confidence()
        if (attributes.containsKey("confidence")) {
            confidence = clamp(number(attributes, "confidence", confidence))
        }
        val uncertainty = number(attributes, "uncertainty", 1.0 - confidence)
        val urgency = number(attributes, "urgency", 0.5)
        val deadlineBreached = truthy(attributes["deadline_breached"])
        val safetyBreached = truthy(attributes["safety_breached"])
        val verificationDue = truthy(attributes["verification_due"])
        val needsMoreInfo = truthy(attributes["needs_more_info"])

        val verb: Verb
        val chosen: ActionOption?
        val rationale: String

        when {
            safetyBlocked(situation) -> {
                verb = Verb.WAIT
                chosen = null
                rationale = "hard safety constraint blocks action"
            }

            (deadlineBreached || safetyBreached) && !byVerb.getValue(Verb.ESCALATE).isEmpty() -> {
                verb = Verb.ESCALATE
                chosen = best(byVerb.getValue(Verb.ESCALATE))
                rationale = if (safetyBreached) {
                    "a hard safety boundary is already breached"
                } else {
                    "a hard deadline or commitment is already breached"
                }
            }

            (needsMoreInfo || uncertainty >= config.askUncertainty) &&
                !byVerb.getValue(Verb.OBSERVE).isEmpty() -> {
                verb = Verb.OBSERVE
                chosen = best(byVerb.getValue(Verb.OBSERVE))
                rationale = "more information is available from a cheap check; look before asking anyone else"
            }

            (uncertainty >= config.askUncertainty || confidence < config.minConfidence) &&
                !byVerb.getValue(Verb.ASK).isEmpty() -> {
                verb = Verb.ASK
                chosen = best(byVerb.getValue(Verb.ASK))
                rationale = if (uncertainty >= config.askUncertainty) {
                    format(
                        "uncertainty %.2f is at or above %.2f",
                        uncertainty,
                        config.askUncertainty,
                    )
                } else {
                    format(
                        "confidence %.2f is below the floor %.2f",
                        confidence,
                        config.minConfidence,
                    )
                }
            }

            verificationDue && !byVerb.getValue(Verb.VERIFY).isEmpty() -> {
                verb = Verb.VERIFY
                chosen = best(byVerb.getValue(Verb.VERIFY))
                rationale = "a previous action has an unverified outcome"
            }

            urgency >= config.actUrgency &&
                confidence >= config.actConfidence &&
                !byVerb.getValue(Verb.ACT).isEmpty() -> {
                verb = Verb.ACT
                chosen = best(byVerb.getValue(Verb.ACT))
                rationale = format(
                    "urgency %.2f and confidence %.2f both clear the act thresholds (%.2f, %.2f)",
                    urgency,
                    confidence,
                    config.actUrgency,
                    config.actConfidence,
                )
            }

            urgency >= config.guideUrgency && !byVerb.getValue(Verb.GUIDE).isEmpty() -> {
                verb = Verb.GUIDE
                chosen = best(byVerb.getValue(Verb.GUIDE))
                rationale = format(
                    "urgency %.2f clears the guide threshold %.2f but not act",
                    urgency,
                    config.guideUrgency,
                )
            }

            !byVerb.getValue(Verb.WAIT).isEmpty() -> {
                verb = Verb.WAIT
                chosen = best(byVerb.getValue(Verb.WAIT))
                rationale = "no higher verb is admissible; keep observing"
            }

            admitted.isNotEmpty() -> {
                chosen = best(admitted)
                verb = chosen.verb
                rationale = "higher verbs were unavailable; best admissible option selected"
            }

            else -> {
                verb = Verb.WAIT
                chosen = null
                rationale = "no admissible option; keep observing"
            }
        }

        val requiresApproval =
            chosen != null &&
                verb == Verb.ACT &&
                (chosen.requiresApproval || chosen.destructive || approvalRequired(situation))
        if (requiresApproval) {
            applied += "approval:human-required"
        }

        val alternatives = alternatives(request.options, chosen, blocked, verb)
        return Decision(
            verb = verb,
            confidence = confidence,
            reasonCode = "policy_rule",
            rationale = rationale,
            decisionId = decisionId,
            situationId = situation.id,
            actionId = chosen?.id,
            alternatives = alternatives,
            constraintsApplied = applied.distinct(),
            requiresApproval = requiresApproval,
            policyVersion = version,
            createdAt = createdAt ?: iso(),
            traceId = traceId,
            score = chosen?.utility ?: 0.0,
            attributes = linkedMapOf(
                "urgency" to round(urgency, 4),
                "uncertainty" to round(uncertainty, 4),
                "deadline_breached" to deadlineBreached,
                "safety_breached" to safetyBreached,
                "needs_more_info" to needsMoreInfo,
            ),
        )
    }

    // --------------------------------------------------------------- admission
    private fun admit(
        situation: Situation,
        options: List<ActionOption>,
        applied: MutableList<String>,
        blocked: MutableMap<String, String>,
    ): List<ActionOption> {
        if (safetyBlocked(situation)) {
            applied += "safety:blocked"
            for (option in options) {
                blocked[option.id] = "blocked by a hard safety constraint"
            }
            return options.filter { it.verb == Verb.WAIT }
        }

        val admitted = mutableListOf<ActionOption>()
        for (option in options) {
            val reason = violation(situation, option)
            if (reason != null) {
                blocked[option.id] = reason
                applied += reason
            } else {
                admitted += option
            }
        }
        return admitted
    }

    private fun violation(situation: Situation, option: ActionOption): String? {
        val pairs = listOf(
            Triple("latency", option.latencyMs.toDouble(), "ms"),
            Triple("cost", option.cost, ""),
            Triple("budget", option.cost, ""),
            Triple("risk", option.risk, ""),
            Triple("interruption", option.interruptCost, ""),
        )
        for ((kind, amount, unit) in pairs) {
            val constraint = situation.constraint(kind) ?: continue
            if (!constraint.hard) continue
            val limit = limit(kind, constraint.value) ?: continue
            if (amount > limit) {
                val suffix = if (unit.isNotEmpty()) " $unit" else ""
                return "blocked by $kind:${constraint.id} ($amount$suffix > $limit$suffix)"
            }
        }
        return null
    }

    private fun limit(kind: String, value: Any?): Double? {
        val raw = when (value) {
            is Map<*, *> -> value["max"] ?: value["value"]
            else -> value
        }
        if (raw is Boolean || raw == null) return null
        val numeric = when (raw) {
            is Number -> raw.toDouble()
            is String -> raw.toDoubleOrNull()
            else -> null
        } ?: return null
        return if (kind == "interruption" && numeric > 1.0) numeric / 100.0 else numeric
    }

    private fun safetyBlocked(situation: Situation): Boolean =
        situation.constraints.any { it.kind == "safety" && it.hard && truthy(it.value) }

    private fun approvalRequired(situation: Situation): Boolean =
        situation.constraints.any { it.kind == "approval" && truthy(it.value) }

    private fun best(options: List<ActionOption>): ActionOption =
        options.sortedWith(compareBy({ -it.utility }, { it.id })).first()

    // ------------------------------------------------------------ explanation
    private fun alternatives(
        options: List<ActionOption>,
        chosen: ActionOption?,
        blocked: Map<String, String>,
        chosenVerb: Verb,
    ): List<Map<String, Any?>> {
        val rows = mutableListOf<Map<String, Any?>>()
        for (option in options) {
            if (chosen != null && option.id == chosen.id) continue
            val reason = when {
                blocked.containsKey(option.id) -> blocked.getValue(option.id)
                option.verb == chosenVerb -> "same verb, lower utility"
                else -> "outranked by ${chosenVerb.value}"
            }
            rows += linkedMapOf(
                "action_id" to option.id,
                "verb" to option.verb.value,
                "name" to option.name,
                "utility" to option.utility,
                "rejected_because" to reason,
            )
        }
        return rows
            .sortedWith(
                compareBy(
                    { -((it["utility"] as Double)) },
                    { it["action_id"] as String },
                ),
            )
            .take(config.maxAlternatives)
    }

    private fun number(attributes: Map<String, Any?>, key: String, default: Double): Double =
        when (val value = attributes[key]) {
            is Number -> value.toDouble()
            is String -> value.toDoubleOrNull() ?: default
            else -> default
        }

    private fun format(pattern: String, vararg args: Double): String =
        String.format(Locale.ROOT, pattern, *args.toTypedArray())
}

/** Functional shortcut for hosts that do not need a policy object. */
fun decideAction(
    request: ActionPolicyInput,
    config: ActionPolicyConfig = ActionPolicyConfig(),
    decisionId: String = "",
    traceId: String = "",
    createdAt: String? = null,
): Decision = ActionPolicy(config).decide(request, decisionId, traceId, createdAt)
