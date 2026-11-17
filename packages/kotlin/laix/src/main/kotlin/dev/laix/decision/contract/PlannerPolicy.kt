package dev.laix.decision.contract

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.support.clamp

/** The smallest contract a policy plugin implements. */
fun interface DecisionPolicy {
    val name: String
        get() = ""

    fun decide(request: DecisionRequest): List<Decision>
}

/** Project the public request onto the planner's input. */
fun toPlannerInput(request: DecisionRequest): PlannerInput =
    PlannerInput(
        subject = request.subject,
        at = request.at,
        situation = request.situation,
        options = request.options,
        signals = request.signals,
        context = request.context,
        attributes = request.attributes,
    )

/**
 * Turn one plan into the public decision shape.
 *
 * This is the single conversion used by [PlannerPolicy]; an adapter that calls
 * a planner directly can use it too, so every planner path returns the same shape.
 * Request attributes are merged first, so planner attributes win on conflict.
 */
fun toDecision(
    plannerResult: PlannerResult,
    request: DecisionRequest,
    decisionId: String = "",
    traceId: String = "",
    policyVersion: String = "planner.v1",
): Decision =
    Decision(
        verb = plannerResult.verb,
        confidence = clamp(plannerResult.confidence),
        reasonCode = plannerResult.reasonCode,
        rationale = plannerResult.rationale,
        decisionId = decisionId,
        traceId = traceId,
        actionId = plannerResult.actionId,
        intent = plannerResult.intent,
        requiresApproval = plannerResult.requiresApproval,
        reversible = plannerResult.reversible,
        undoHint = plannerResult.undoHint,
        score = plannerResult.score,
        alternatives = plannerResult.alternatives,
        attributes = request.attributes + plannerResult.attributes,
        policyVersion = policyVersion,
    )

/** Wrap any [Planner] as a policy. */
class PlannerPolicy(
    val planner: Planner,
    override val name: String = "planner.v1",
) : DecisionPolicy {
    val version: String
        get() = name

    override fun decide(request: DecisionRequest): List<Decision> =
        decide(request, decisionId = "", traceId = "")

    fun decide(
        request: DecisionRequest,
        decisionId: String,
        traceId: String,
    ): List<Decision> {
        val plannerResult = planner.solve(toPlannerInput(request))
        return listOf(
            toDecision(
                plannerResult,
                request,
                decisionId = decisionId,
                traceId = traceId,
                policyVersion = name,
            ),
        )
    }
}
