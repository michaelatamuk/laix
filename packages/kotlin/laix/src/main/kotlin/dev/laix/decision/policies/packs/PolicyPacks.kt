package dev.laix.decision.policies.packs

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.truthy
import java.util.Locale

/** Choose only inside the hard risk limit. */
class SafetyConstrainedPolicy : DecisionPolicy {
    override val name: String = "safety-constrained.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        if (truthy(policyValue(request, "safety_blocked", false))) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "safety_blocked",
                    "a hard safety constraint blocks action",
                    1.0,
                ),
            )
        }

        val riskLimit = policyNumber(request, "risk_limit", 0.2)
        val options = policyMaps(policyValue(request, "options"))
        val safe = options.filter { mapNumber(it, "risk") <= riskLimit }
        if (safe.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "no_safe_option",
                    "every available option exceeds the risk limit",
                    0.9,
                ),
            )
        }

        val best = safe.maxByOrNull {
            mapNumber(it, "benefit") - mapNumber(it, "risk") - 0.1 * mapNumber(it, "cost")
        }!!
        val benefit = mapNumber(best, "benefit")
        val risk = mapNumber(best, "risk")
        val requiresApproval = truthy(best["requires_approval"]) || truthy(best["destructive"])
        return listOf(
            policyDecision(
                name,
                if (benefit >= 0.5) Verb.ACT else Verb.GUIDE,
                if (benefit >= 0.5) "safe_action" else "safe_to_show",
                String.format(
                    Locale.ROOT,
                    "choose %s with risk %.2f inside the limit %.2f",
                    mapText(best, "id", "?"),
                    risk,
                    riskLimit,
                ),
                minOf(0.98, 0.55 + benefit * 0.4),
                intent = Intent("act", mapOf("id" to mapText(best, "id"))),
                score = round6(benefit - risk),
                requiresApproval = requiresApproval,
                actionId = mapText(best, "id"),
            ),
        )
    }
}

/** Confirm that an action did what it claimed. */
class VerificationPolicy : DecisionPolicy {
    override val name: String = "verification.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        if (truthy(policyValue(request, "verified", false))) {
            return listOf(
                policyDecision(name, Verb.WAIT, "already_verified", "the outcome is already confirmed", 1.0),
            )
        }

        val confidence = policyNumber(request, "confidence", 0.5)
        val required = policyNumber(request, "required_confidence", 0.8)
        val due = truthy(policyValue(request, "verification_due", true))
        val budget = policyNumber(request, "budget", Double.POSITIVE_INFINITY)
        val checks = policyMaps(policyValue(request, "checks"))
        val target = policyValue(request, "escalation_target", "human").toString()

        if (!due && confidence >= required) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "verification_not_needed",
                    String.format(
                        Locale.ROOT,
                        "confidence %.2f meets the requirement %.2f",
                        confidence,
                        required,
                    ),
                    confidence,
                ),
            )
        }

        if (checks.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ESCALATE,
                    "no_verification_path",
                    "no check can confirm the outcome; ask a person",
                    0.6,
                    intent = Intent(
                        "handover",
                        mapOf("target" to target, "reason" to "no verification path"),
                    ),
                ),
            )
        }

        val affordable = checks.filter { mapNumber(it, "cost") <= budget }
        if (affordable.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ESCALATE,
                    "no_verification_budget",
                    "every check costs more than the verification budget",
                    0.6,
                    intent = Intent(
                        "handover",
                        mapOf("target" to target, "reason" to "verification budget exhausted"),
                    ),
                ),
            )
        }

        val best = affordable.maxByOrNull {
            mapNumber(it, "confidence_gain", mapNumber(it, "information_gain")) /
                maxOf(mapNumber(it, "cost"), 0.001)
        }!!
        val gain = mapNumber(best, "confidence_gain", mapNumber(best, "information_gain"))
        if (gain <= 0) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ESCALATE,
                    "no_verification_path",
                    "no available check would raise confidence",
                    0.6,
                    intent = Intent(
                        "handover",
                        mapOf("target" to target, "reason" to "no useful verification path"),
                    ),
                ),
            )
        }

        return listOf(
            policyDecision(
                name,
                Verb.VERIFY,
                "verify_outcome",
                "run check ${mapText(best, "id", "?")} to confirm the outcome",
                minOf(0.95, confidence + gain),
                intent = Intent("verify", mapOf("id" to mapText(best, "id"))),
                score = round6(gain),
                actionId = mapText(best, "id"),
            ),
        )
    }
}

/** Ask the question that best reduces uncertainty. */
class PreferenceElicitationPolicy : DecisionPolicy {
    override val name: String = "preference-elicitation.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        val uncertainty = policyNumber(request, "uncertainty", 0.5)
        val threshold = policyNumber(request, "uncertainty_threshold", 0.2)
        val questions = policyMaps(policyValue(request, "questions"))

        if (uncertainty <= threshold) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ACT,
                    "preference_known",
                    "uncertainty is low enough to choose without another question",
                    1.0 - uncertainty,
                ),
            )
        }
        if (questions.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "no_question",
                    "no useful question is available",
                    0.5,
                ),
            )
        }

        val best = questions.maxByOrNull {
            mapNumber(it, "information_gain") / maxOf(mapNumber(it, "cost"), 0.001)
        }!!
        val gain = mapNumber(best, "information_gain")
        return listOf(
            policyDecision(
                name,
                Verb.ASK,
                "ask_preference",
                "ask ${mapText(best, "id", "?")} to reduce preference uncertainty",
                minOf(0.95, 0.5 + gain),
                intent = Intent("ask_question", mapOf("id" to mapText(best, "id"))),
                score = round6(gain),
                actionId = mapText(best, "id"),
            ),
        )
    }
}

/** Choose the next look when uncertainty is high. */
class ActivePerceptionPolicy : DecisionPolicy {
    override val name: String = "active-perception.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        val uncertainty = policyNumber(request, "uncertainty", 0.5)
        val minimum = policyNumber(request, "min_information_gain", 0.2)
        val budget = policyNumber(request, "budget", Double.POSITIVE_INFINITY)
        val observations = policyMaps(policyValue(request, "observations"))

        if (uncertainty < minimum) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "uncertainty_low",
                    "uncertainty is low enough to decide without another look",
                    1.0 - uncertainty,
                ),
            )
        }
        if (observations.isEmpty()) {
            return listOf(
                policyDecision(name, Verb.WAIT, "no_observation", "no observation is available", 0.4),
            )
        }

        val best = observations.maxByOrNull {
            mapNumber(it, "information_gain") * uncertainty / maxOf(mapNumber(it, "cost"), 0.001)
        }!!
        val gain = mapNumber(best, "information_gain") * uncertainty
        val cost = mapNumber(best, "cost")
        if (gain < minimum || cost > budget) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "observation_not_worth_it",
                    "the available observation costs more than it is expected to resolve",
                    0.5,
                ),
            )
        }
        return listOf(
            policyDecision(
                name,
                Verb.OBSERVE,
                "observe_for_information",
                "take observation ${mapText(best, "id", "?")} to reduce uncertainty",
                minOf(0.95, 0.5 + gain),
                intent = Intent("observe", mapOf("id" to mapText(best, "id"))),
                score = round6(gain),
                actionId = mapText(best, "id"),
            ),
        )
    }
}

/** Choose a plan after the old one broke. */
class ReplanningPolicy : DecisionPolicy {
    override val name: String = "replanning.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        val plans = policyMaps(policyValue(request, "plans"))
        val minSuccess = policyNumber(request, "min_success", 0.5)
        val maxCost = policyNumber(request, "max_cost", Double.POSITIVE_INFINITY)
        val riskWeight = policyNumber(request, "risk_weight", 1.0)

        val feasible = plans.filter {
            mapNumber(it, "success_probability") >= minSuccess && mapNumber(it, "cost") <= maxCost
        }
        if (feasible.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ASK,
                    "no_feasible_plan",
                    "no plan meets the success and cost limits; ask for a changed constraint",
                    0.8,
                ),
            )
        }

        val best = feasible.maxByOrNull {
            mapNumber(it, "success_probability") -
                riskWeight * mapNumber(it, "cost") -
                mapNumber(it, "deadline_risk")
        }!!
        val success = mapNumber(best, "success_probability")
        return listOf(
            policyDecision(
                name,
                Verb.ACT,
                "replan",
                String.format(
                    Locale.ROOT,
                    "adopt %s with success probability %.2f",
                    mapText(best, "id", "?"),
                    success,
                ),
                minOf(0.98, 0.5 + success * 0.4),
                intent = Intent("adopt_plan", mapOf("id" to mapText(best, "id"))),
                score = success,
                requiresApproval = truthy(best["requires_approval"]),
                actionId = mapText(best, "id"),
            ),
        )
    }
}

/** Decide when a situation must leave the current owner. */
class EscalationPolicy : DecisionPolicy {
    override val name: String = "escalation.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        if (truthy(policyValue(request, "resolved", false))) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "resolved",
                    "the situation is resolved; no escalation is needed",
                    1.0,
                ),
            )
        }

        val severity = policyNumber(request, "severity", 0.0)
        val threshold = policyNumber(request, "severity_threshold", 0.8)
        val attempts = policyNumber(request, "attempts", 0.0).toInt()
        val maxAttempts = policyNumber(request, "max_attempts", 3.0).toInt()
        val confidence = policyNumber(request, "confidence", 1.0)
        val minConfidence = policyNumber(request, "min_confidence", 0.5)
        val slaBreached = truthy(policyValue(request, "sla_breached", false))

        val reasons = mutableListOf<String>()
        if (severity >= threshold) {
            reasons += String.format(Locale.ROOT, "severity %.2f reached %.2f", severity, threshold)
        }
        if (attempts >= maxAttempts) reasons += "attempts $attempts reached $maxAttempts"
        if (confidence < minConfidence) {
            reasons += String.format(
                Locale.ROOT,
                "confidence %.2f is below %.2f",
                confidence,
                minConfidence,
            )
        }
        if (slaBreached) reasons += "the service level is breached"

        if (reasons.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "within_limits",
                    "severity, attempts and confidence are still within limits",
                    confidence,
                ),
            )
        }

        val target = policyValue(request, "target", "")?.toString().orEmpty()
        val rationale = reasons.joinToString("; ")
        if (target.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ASK,
                    "target_required",
                    "$rationale; no escalation target is known",
                    0.7,
                ),
            )
        }

        return listOf(
            policyDecision(
                name,
                Verb.ESCALATE,
                "escalate_to_target",
                "$rationale; hand over to $target",
                minOf(0.98, maxOf(severity, 1.0 - confidence)),
                intent = Intent("handover", mapOf("target" to target, "reason" to rationale)),
                score = round6(severity),
                actionId = target,
            ),
        )
    }
}

/** Accept, counter or walk from a simple offer. */
class NegotiationPolicy : DecisionPolicy {
    override val name: String = "negotiation.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        val offer = policyNumber(request, "offer", 0.0)
        val reservation = policyNumber(request, "reservation", 0.0)
        val target = policyNumber(request, "target", reservation)
        val round = policyNumber(request, "round", 1.0).toInt()
        val maxRounds = policyNumber(request, "max_rounds", 5.0).toInt()

        if (offer >= reservation) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ACT,
                    "accept_offer",
                    String.format(
                        Locale.ROOT,
                        "the offer %.2f meets the reservation %.2f",
                        offer,
                        reservation,
                    ),
                    0.95,
                    intent = Intent("accept_offer", mapOf("amount" to offer)),
                    actionId = "accept_offer",
                ),
            )
        }
        if (round >= maxRounds) {
            return listOf(
                policyDecision(
                    name,
                    Verb.ESCALATE,
                    "round_limit",
                    "the round limit is reached without an acceptable offer",
                    0.8,
                ),
            )
        }
        val counter = maxOf(reservation, (offer + target) / 2.0)
        return listOf(
            policyDecision(
                name,
                Verb.ACT,
                "counter_offer",
                String.format(
                    Locale.ROOT,
                    "counter at %.2f, between the offer %.2f and target %.2f",
                    counter,
                    offer,
                    target,
                ),
                0.7,
                intent = Intent("counter_offer", mapOf("amount" to counter)),
                actionId = "counter_offer",
            ),
        )
    }
}

/** Choose a portfolio of work under a budget. */
class AllocationPolicy : DecisionPolicy {
    override val name: String = "allocation.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        val requests = policyMaps(policyValue(request, "requests"))
        val budget = policyNumber(request, "budget", 0.0)
        val maxRisk = policyNumber(request, "max_risk", 1.0)

        val candidates = requests
            .filter { mapNumber(it, "cost") <= budget && mapNumber(it, "risk") <= maxRisk }
            .sortedByDescending { mapNumber(it, "value") / maxOf(mapNumber(it, "cost"), 0.001) }

        val chosen = mutableListOf<Map<String, Any?>>()
        var spent = 0.0
        var totalValue = 0.0
        for (item in candidates) {
            val cost = mapNumber(item, "cost")
            if (spent + cost > budget) continue
            chosen += item
            spent += cost
            totalValue += mapNumber(item, "value")
        }

        if (chosen.isEmpty()) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "nothing_affordable",
                    "no request fits the budget and risk limit",
                    0.8,
                ),
            )
        }
        return listOf(
            policyDecision(
                name,
                Verb.ACT,
                "allocate",
                String.format(
                    Locale.ROOT,
                    "fund %d request(s) for value %.2f within budget %.2f",
                    chosen.size,
                    totalValue,
                    budget,
                ),
                minOf(0.95, 0.5 + totalValue / maxOf(budget, 1.0) * 0.2),
                intent = Intent("allocate", mapOf("ids" to chosen.map { mapText(it, "id") })),
                score = round6(totalValue),
                requiresApproval = truthy(policyValue(request, "requires_approval", false)),
            ),
        )
    }
}
