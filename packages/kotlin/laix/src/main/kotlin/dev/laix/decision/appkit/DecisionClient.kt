package dev.laix.decision.appkit

import dev.laix.decision.Route
import dev.laix.decision.annotateConfidence
import dev.laix.decision.appkit.delivery.DeliveryPort
import dev.laix.decision.appkit.delivery.DeliveryReceipt
import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.records.ExecutionReceipt
import dev.laix.decision.appkit.runtime.DecisionRuntime
import dev.laix.decision.appkit.streaming.StreamSession
import dev.laix.decision.attributesFor
import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.SCHEMA_VERSION
import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.policies.DecisionPolicyRegistry
import dev.laix.decision.policies.action.ACTION_POLICY_VERSION
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.support.utcNow
import java.time.OffsetDateTime
import dev.laix.decision.select

/**
 * The public DecisionClient: one request in, one decision shape out.
 *
 * This keeps the orchestrator, the built-in request routing and the
 * normalisation of custom policy results into the one `Decision` shape.
 */
class DecisionClient(
    val runtime: DecisionRuntime = DecisionRuntime(),
    policy: DecisionPolicy? = null,
) : DecisionPolicy {
    override val name: String
        get() = activePolicy?.name?.ifEmpty { null } ?: "builtin"

    private val decisions = mutableListOf<Decision>()
    private val registry = DecisionPolicyRegistry()
    private var activePolicy: DecisionPolicy? = null

    init {
        if (policy != null) {
            val name = policy.name.ifEmpty { "custom" }
            registry.register(name, policy)
            activePolicy = policy
        }
    }

    fun registerPolicy(name: String, policy: DecisionPolicy) {
        registry.register(name, policy)
    }

    fun usePolicy(name: String) {
        activePolicy = registry.get(name)
    }

    fun policies(): List<String> = registry.names()

    override fun decide(request: DecisionRequest): List<Decision> {
        val route = select(request, activePolicy)
        val result = when (route) {
            Route.ACTION -> {
                val situation = request.situation
                    ?: throw IllegalArgumentException("action selection needs a situation")
                listOf(
                    annotateConfidence(
                        runtime.decide(situation, request.options, attributesFor(request)),
                        request,
                    ),
                )
            }
            Route.POLICY -> dev.laix.decision.decide(request, activePolicy)
            Route.ATTENTION -> dev.laix.decision.decide(request)
        }
        decisions += result
        return result
    }

    /** Create a stream session backed by this layer's decision path. */
    fun stream(
        streamId: String = "",
        capacity: Int = 32,
        onFull: String = "latest_wins",
        late: String = "drop",
        cooldownMs: Long = 0,
        hysteresisMs: Long = 0,
        dedupeMs: Long = 0,
        maxDecisionsPerWindow: Int? = null,
        budgetWindowMs: Long = 1000,
        latencySamples: Int = 256,
        trace: Boolean = true,
        recorder: ((Decision) -> Unit)? = null,
        humanAttentionBudget: HumanAttentionBudget? = null,
        clock: () -> OffsetDateTime = { utcNow() },
    ): StreamSession =
        StreamSession(
            decide = this::decide,
            streamId = streamId,
            capacity = capacity,
            onFull = onFull,
            late = late,
            cooldownMs = cooldownMs,
            hysteresisMs = hysteresisMs,
            dedupeMs = dedupeMs,
            maxDecisionsPerWindow = maxDecisionsPerWindow,
            budgetWindowMs = budgetWindowMs,
            latencySamples = latencySamples,
            trace = trace,
            recorder = recorder,
            humanAttentionBudget = humanAttentionBudget,
            clock = clock,
        )

    fun execute(
        decision: Decision,
        actor: String,
        approver: String? = null,
        context: Map<String, Any?>? = null,
        idempotencyKey: String? = null,
    ): ExecutionReceipt =
        runtime.execute(
            decision = decision,
            actor = actor,
            approver = approver,
            context = context,
            idempotencyKey = idempotencyKey,
        )

    fun measure(
        decision: Decision,
        metric: String,
        before: Double,
        after: Double,
        attributed: Boolean = false,
        direction: String = "higher-better",
        evidence: Map<String, Any?> = emptyMap(),
        note: String = "",
        label: String? = null,
    ): Outcome =
        runtime.measure(
            decisionId = decision.decisionId,
            metric = metric,
            before = before,
            after = after,
            attributed = attributed,
            direction = direction,
            evidence = evidence,
            note = note,
            label = label,
        )

    fun deliver(
        decision: Decision,
        port: DeliveryPort,
        message: Any?,
        channel: String = "default",
    ): DeliveryReceipt = port.deliver(decision, message, channel)

    fun status(): Map<String, Any?> =
        linkedMapOf(
            "schemaVersion" to SCHEMA_VERSION,
            "policy" to (activePolicy?.name?.ifEmpty { null } ?: "builtin"),
            "policyVersion" to (activePolicy?.name?.ifEmpty { null } ?: ACTION_POLICY_VERSION),
            "decisions" to decisions.size,
            "policies" to registry.names(),
        )

    fun explain(decision: Decision): Map<String, Any?> =
        linkedMapOf(
            "verb" to decision.verb.value,
            "reasonCode" to decision.reasonCode,
            "rationale" to decision.rationale,
            "confidence" to decision.confidence,
            "evidence" to decision.evidence.map { it.toMap() },
            "score" to decision.score,
            "breakdown" to decision.breakdown?.toMap(),
            "requiresApproval" to decision.requiresApproval,
            "deliver" to decision.deliver,
            "record" to decision.record,
            "traceId" to decision.traceId,
        )

    fun bridge(): ExecutionBridge = runtime.bridge
}
