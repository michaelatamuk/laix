package dev.laix.decision.policies.packs

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.TargetMode

/** Apply one target mode and recipient set to another policy's decisions. */
class TargetedPolicy(
    private val policy: DecisionPolicy,
    val target: String = "request",
    val recipients: List<String> = emptyList(),
) : DecisionPolicy {
    init {
        if (target != "request") TargetMode.from(target)
    }

    override val name: String = "targeted.v1"
    override val version: String = policy.version ?: name

    override fun decide(request: DecisionRequest): List<Decision> {
        val targetMode = if (target == "request") request.target else TargetMode.from(target)
        val to = recipients.ifEmpty { request.recipients }
        return policy.decide(request).map {
            it.copy(target = targetMode, recipients = to)
        }
    }
}

/** Apply a group target and remove private data before sharing. */
class GroupPolicy(
    private val policy: DecisionPolicy,
    val target: String = "some",
    val recipients: List<String> = emptyList(),
    privateAttributes: List<String> = emptyList(),
    privateEvidence: List<String> = emptyList(),
    val rationale: String? = null,
    val undoHint: String? = null,
) : DecisionPolicy {
    private val privateAttributes: Set<String> = privateAttributes.toSet()
    private val privateEvidence: Set<String> = privateEvidence.toSet()

    init {
        TargetMode.from(target)
    }

    override val name: String = "group.v1"
    override val version: String = policy.version ?: name

    override fun decide(request: DecisionRequest): List<Decision> {
        val to = recipients.ifEmpty { request.recipients }
        return policy.decide(request).map { mask(it, to) }
    }

    @Suppress("UNCHECKED_CAST")
    private fun mask(decision: Decision, recipients: List<String>): Decision {
        val evidence = decision.evidence.filter { item ->
            val markers = setOf(item.id, item.kind, item.source ?: "")
            markers.intersect(privateEvidence).isEmpty()
        }
        val intent = decision.intent?.let {
            Intent(it.capability, maskValue(it.args) as Map<String, Any?>)
        }
        return decision.copy(
            target = TargetMode.from(target),
            recipients = recipients,
            rationale = rationale ?: decision.rationale,
            undoHint = undoHint ?: decision.undoHint,
            evidence = evidence,
            intent = intent,
            alternatives = decision.alternatives.map { maskValue(it) as Map<String, Any?> },
            attributes = maskValue(decision.attributes) as Map<String, Any?>,
        )
    }

    @Suppress("UNCHECKED_CAST")
    private fun maskValue(value: Any?): Any? =
        when (value) {
            is Map<*, *> -> value.entries
                .filter { it.key !in privateAttributes }
                .associate { it.key.toString() to maskValue(it.value) }
            is List<*> -> value.map { maskValue(it) }
            is Set<*> -> value.map { maskValue(it) }.toSet()
            is Array<*> -> value.map { maskValue(it) }
            else -> value
        }
}
