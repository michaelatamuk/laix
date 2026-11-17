package dev.laix.decision.appkit.runtime

import dev.laix.decision.appkit.execution.ApprovalRequired
import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.records.ExecutionReceipt
import dev.laix.decision.appkit.records.Trace
import dev.laix.decision.appkit.state.ExperienceState
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.Situation
import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.outcomes.OutcomeLedger
import dev.laix.decision.policies.action.ActionPolicy
import dev.laix.decision.policies.action.ActionPolicyInput
import dev.laix.decision.support.newId

/**
 * The runtime facade an app talks to.
 *
 * Wires the reusable pieces together: observe -> state -> policy -> execution -> outcome.
 * Every decision gets a trace, every execution gets a receipt, and every measured
 * change is recorded against the decision that caused it.
 */
class DecisionRuntime(
    var state: ExperienceState = ExperienceState(subject = ""),
    val policy: ActionPolicy = ActionPolicy(),
    val bridge: ExecutionBridge = ExecutionBridge(),
    val outcomes: OutcomeLedger = OutcomeLedger(),
    private val idFactory: (String) -> String = ::newId,
) {
    private val actions = LinkedHashMap<String, ActionOption>()
    private val decisions = LinkedHashMap<String, Decision>()
    private val traces = LinkedHashMap<String, Trace>()
    private val traceByDecision = LinkedHashMap<String, String>()
    private val receiptIds = mutableListOf<String>()

    fun observe(observation: Observation) {
        state.observe(observation)
    }

    fun decide(
        situation: Situation,
        options: List<ActionOption>,
        attributes: Map<String, Any?> = emptyMap(),
    ): Decision {
        val decisionId = idFactory("DEC")
        val traceId = idFactory("TRC")
        val request = ActionPolicyInput(
            situation = situation,
            options = options,
            attributes = attributes,
        )
        val decision = policy.decide(request, decisionId = decisionId, traceId = traceId)
        decisions[decision.decisionId] = decision
        for (option in request.options) actions[option.id] = option
        state.record(decision)
        traces[traceId] = Trace(id = traceId, decisionId = decision.decisionId).withEvent(
            "situation",
            linkedMapOf(
                "subject" to situation.subject,
                "phase" to situation.phase,
                "horizon" to situation.horizon,
                "confidence" to Math.round(situation.confidence() * 10000.0) / 10000.0,
                "observations" to situation.observations.size,
                "beliefs" to situation.beliefs.size,
                "options" to request.options.map { it.id },
                "attributes" to (situation.attributes + request.attributes),
            ),
            at = situation.at,
        )
        appendTrace(
            decision,
            "decided",
            linkedMapOf(
                "verb" to decision.verb.value,
                "action" to decision.actionId,
                "rationale" to decision.rationale,
                "policy" to decision.policyVersion,
                "requiresApproval" to decision.requiresApproval,
            ),
        )
        traceByDecision[decision.decisionId] = traceId
        return decision
    }

    fun execute(
        decision: Decision,
        actor: String,
        approver: String? = null,
        context: Map<String, Any?>? = null,
        action: ActionOption? = null,
        idempotencyKey: String? = null,
    ): ExecutionReceipt {
        val resolved = action ?: decision.actionId?.let { actions[it] }
        val receipt = try {
            bridge.execute(
                decision = decision,
                action = resolved,
                actor = actor,
                approver = approver,
                context = context,
                idempotencyKey = idempotencyKey,
            )
        } catch (exception: ApprovalRequired) {
            bridge.refuse(decision, resolved, actor, exception.message ?: "approval required").also {
                appendTrace(
                    decision,
                    "approval.required",
                    mapOf("actor" to actor, "reason" to exception.message),
                )
            }
        }
        receiptIds += receipt.id
        appendTrace(
            decision,
            "execution.${receipt.status}",
            linkedMapOf(
                "receipt" to receipt.id,
                "actor" to actor,
                "approvedBy" to approver,
                "error" to receipt.error,
            ),
        )
        return receipt
    }

    fun cancel(receiptId: String, actor: String, reason: String = ""): ExecutionReceipt {
        val receipt = bridge.cancel(receiptId, actor, reason)
        decisions[receipt.decisionId]?.let {
            appendTrace(
                it,
                "execution.cancelled",
                mapOf("receipt" to receipt.id, "actor" to actor, "reason" to reason),
            )
        }
        return receipt
    }

    fun undo(receiptId: String, actor: String): ExecutionReceipt {
        val receipt = bridge.undo(receiptId, actor)
        decisions[receipt.decisionId]?.let {
            appendTrace(it, "execution.undone", mapOf("receipt" to receipt.id, "actor" to actor))
        }
        return receipt
    }

    fun measure(
        decisionId: String,
        metric: String,
        before: Double,
        after: Double,
        attributed: Boolean = false,
        direction: String = "higher-better",
        evidence: Map<String, Any?> = emptyMap(),
        note: String = "",
        label: String? = null,
    ): Outcome {
        val outcome = outcomes.record(
            decisionId = decisionId,
            metric = metric,
            before = before,
            after = after,
            attributed = attributed,
            direction = direction,
            evidence = evidence,
            note = note,
            label = label,
        )
        decisions[decisionId]?.let {
            appendTrace(
                it,
                "outcome.measured",
                linkedMapOf(
                    "metric" to metric,
                    "delta" to outcome.delta,
                    "label" to outcome.label,
                    "attributed" to attributed,
                ),
            )
        }
        return outcome
    }

    fun trace(decisionId: String): Trace {
        val traceId = traceByDecision[decisionId]
            ?: throw NoSuchElementException(decisionId)
        return traces[traceId] ?: throw NoSuchElementException(decisionId)
    }

    fun decision(decisionId: String): Decision =
        decisions[decisionId] ?: throw NoSuchElementException(decisionId)

    fun actionFor(decision: Decision): ActionOption? =
        decision.actionId?.let { actions[it] }

    fun receipts(): List<ExecutionReceipt> = receiptIds.map { bridge.get(it) }

    fun stats(): Map<String, Any?> {
        val verbs = decisions.values
            .groupingBy { it.verb.value }
            .eachCount()
            .toSortedMap()
        val statuses = receipts()
            .groupingBy { it.status }
            .eachCount()
            .toSortedMap()
        return linkedMapOf(
            "decisions" to decisions.size,
            "verbs" to verbs,
            "executions" to statuses,
            "outcomes" to outcomes.summary(),
            "policyVersion" to policy.version,
        )
    }

    private fun appendTrace(
        decision: Decision,
        stage: String,
        detail: Map<String, Any?> = emptyMap(),
    ) {
        val traceId = decision.traceId
        var trace = traces[traceId]
        if (trace == null) {
            trace = Trace(
                id = traceId.ifEmpty { idFactory("TRC") },
                decisionId = decision.decisionId,
            )
        }
        traces[trace.id] = trace.withEvent(stage, detail)
        traceByDecision[decision.decisionId] = trace.id
    }

}
