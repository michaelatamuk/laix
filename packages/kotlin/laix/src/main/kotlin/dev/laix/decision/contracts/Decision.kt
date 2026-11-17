package dev.laix.decision.contracts

import dev.laix.decision.support.clamp
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.pythonRepr
import dev.laix.decision.support.toJson
import dev.laix.decision.support.truthy

/** Lifecycle of a decision that belongs to a stream. */
enum class DecisionStatus(val value: String) {
    FINAL("final"),
    PROVISIONAL("provisional"),
    SUPERSEDED("superseded");

    companion object {
        fun from(value: String): DecisionStatus =
            entries.firstOrNull { it.value == value }
                ?: throw IllegalArgumentException("unknown decision status: $value")
    }
}

/** Who receives a decision: one, some, all, a peer or gathered from many. */
enum class TargetMode(val value: String) {
    ONE("one"),
    SOME("some"),
    ALL("all"),
    PEER("peer"),
    GATHER("gather");

    companion object {
        fun from(value: String): TargetMode =
            entries.firstOrNull { it.value == value }
                ?: throw IllegalArgumentException("unknown target mode: $value")
    }
}

/**
 * The one decision shape returned by every policy, `decide` and `DecisionClient`.
 *
 * `confidence` is clamped on construction and on [copy], matching the Python
 * record's `__post_init__`. It is declared as an ordinary class rather than a
 * data class so the property can be clamped instead of merely validated.
 */
class Decision(
    val verb: Verb,
    confidence: Double,
    val reasonCode: String,
    val rationale: String,
    val decisionId: String = "",
    val situationId: String = "",
    val policyVersion: String = "",
    val actionId: String? = null,
    val evidence: List<EvidenceRef> = emptyList(),
    val requiresApproval: Boolean = false,
    val score: Double? = null,
    val breakdown: ScoreBreakdown? = null,
    val intent: Intent? = null,
    val costOfWaiting: Double = 0.0,
    val reversible: Boolean = false,
    val undoHint: String? = null,
    val traceId: String = "",
    val deliver: Boolean = true,
    val record: Boolean = true,
    val createdAt: String? = null,
    val confidenceSource: String = "",
    val calibrated: Boolean = false,
    val alternatives: List<Map<String, Any?>> = emptyList(),
    val constraintsApplied: List<String> = emptyList(),
    val attributes: Map<String, Any?> = emptyMap(),
    val target: TargetMode = TargetMode.ONE,
    val recipients: List<String> = emptyList(),
    val streamId: String = "",
    val eventTime: String? = null,
    val deadline: String? = null,
    val validUntil: String? = null,
    val supersedes: String? = null,
    val revision: Int = 0,
    val status: DecisionStatus = DecisionStatus.FINAL,
    val schemaVersion: String = SCHEMA_VERSION,
) {
    /** Always in `0..1`; the Python record clamps rather than rejects. */
    val confidence: Double = clamp(confidence)

    /** A host-neutral basis for a decision record or explain view. */
    fun basis(): List<Map<String, Any?>> {
        val rows = mutableListOf<Map<String, Any?>>(
            linkedMapOf("kind" to "reason", "ref" to reasonCode, "note" to rationale),
        )
        for (item in evidence) {
            rows += linkedMapOf(
                "kind" to item.kind,
                "ref" to item.id,
                "note" to (item.quote ?: ""),
                "source" to (item.source ?: ""),
            )
        }
        intent?.let {
            rows += linkedMapOf(
                "kind" to "intent",
                "ref" to it.capability,
                "note" to pythonRepr(it.args),
            )
        }
        for (item in constraintsApplied) {
            rows += linkedMapOf("kind" to "constraint", "ref" to item, "note" to "")
        }
        return rows
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "verb" to verb.value,
            "confidence" to confidence,
            "reason_code" to reasonCode,
            "rationale" to rationale,
            "decision_id" to decisionId,
            "situation_id" to situationId,
            "policy_version" to policyVersion,
            "action_id" to actionId,
            "evidence" to evidence.map { it.toMap() },
            "requires_approval" to requiresApproval,
            "score" to score,
            "breakdown" to breakdown?.toMap(),
            "intent" to intent?.asDict(),
            "cost_of_waiting" to costOfWaiting,
            "reversible" to reversible,
            "undo_hint" to undoHint,
            "trace_id" to traceId,
            "deliver" to deliver,
            "record" to record,
            "created_at" to createdAt,
            "confidence_source" to confidenceSource,
            "calibrated" to calibrated,
            "alternatives" to alternatives,
            "constraints_applied" to constraintsApplied,
            "attributes" to attributes,
            "target" to target.value,
            "recipients" to recipients,
            "stream_id" to streamId,
            "event_time" to eventTime,
            "deadline" to deadline,
            "valid_until" to validUntil,
            "supersedes" to supersedes,
            "revision" to revision,
            "status" to status.value,
            "schema_version" to schemaVersion,
        )

    /** Serialize to the published snake_case JSON shape. */
    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    @Suppress("LongParameterList")
    fun copy(
        verb: Verb = this.verb,
        confidence: Double = this.confidence,
        reasonCode: String = this.reasonCode,
        rationale: String = this.rationale,
        decisionId: String = this.decisionId,
        situationId: String = this.situationId,
        policyVersion: String = this.policyVersion,
        actionId: String? = this.actionId,
        evidence: List<EvidenceRef> = this.evidence,
        requiresApproval: Boolean = this.requiresApproval,
        score: Double? = this.score,
        breakdown: ScoreBreakdown? = this.breakdown,
        intent: Intent? = this.intent,
        costOfWaiting: Double = this.costOfWaiting,
        reversible: Boolean = this.reversible,
        undoHint: String? = this.undoHint,
        traceId: String = this.traceId,
        deliver: Boolean = this.deliver,
        record: Boolean = this.record,
        createdAt: String? = this.createdAt,
        confidenceSource: String = this.confidenceSource,
        calibrated: Boolean = this.calibrated,
        alternatives: List<Map<String, Any?>> = this.alternatives,
        constraintsApplied: List<String> = this.constraintsApplied,
        attributes: Map<String, Any?> = this.attributes,
        target: TargetMode = this.target,
        recipients: List<String> = this.recipients,
        streamId: String = this.streamId,
        eventTime: String? = this.eventTime,
        deadline: String? = this.deadline,
        validUntil: String? = this.validUntil,
        supersedes: String? = this.supersedes,
        revision: Int = this.revision,
        status: DecisionStatus = this.status,
        schemaVersion: String = this.schemaVersion,
    ): Decision =
        Decision(
            verb = verb,
            confidence = confidence,
            reasonCode = reasonCode,
            rationale = rationale,
            decisionId = decisionId,
            situationId = situationId,
            policyVersion = policyVersion,
            actionId = actionId,
            evidence = evidence,
            requiresApproval = requiresApproval,
            score = score,
            breakdown = breakdown,
            intent = intent,
            costOfWaiting = costOfWaiting,
            reversible = reversible,
            undoHint = undoHint,
            traceId = traceId,
            deliver = deliver,
            record = record,
            createdAt = createdAt,
            confidenceSource = confidenceSource,
            calibrated = calibrated,
            alternatives = alternatives,
            constraintsApplied = constraintsApplied,
            attributes = attributes,
            target = target,
            recipients = recipients,
            streamId = streamId,
            eventTime = eventTime,
            deadline = deadline,
            validUntil = validUntil,
            supersedes = supersedes,
            revision = revision,
            status = status,
            schemaVersion = schemaVersion,
        )

    override fun equals(other: Any?): Boolean =
        other is Decision && other.toMap() == toMap()

    override fun hashCode(): Int = toMap().hashCode()

    override fun toString(): String = "Decision(${toMap()})"

    companion object {
        fun fromJson(text: String): Decision = fromMap(parseJsonObject(text))

        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): Decision {
            fun text(key: String): String? = payload[key]?.toString()
            fun list(key: String): List<Any?> = payload[key] as? List<Any?> ?: emptyList()

            return Decision(
                verb = Verb.from(text("verb") ?: Verb.WAIT.value),
                confidence = (payload["confidence"] as? Number)?.toDouble() ?: 0.0,
                reasonCode = text("reason_code") ?: "",
                rationale = text("rationale") ?: "",
                decisionId = text("decision_id") ?: "",
                situationId = text("situation_id") ?: "",
                policyVersion = text("policy_version") ?: "",
                actionId = text("action_id"),
                evidence = list("evidence").mapNotNull { item ->
                    (item as? Map<*, *>)?.let {
                        EvidenceRef.fromMap(it.entries.associate { e -> e.key.toString() to e.value })
                    }
                },
                requiresApproval = truthy(payload["requires_approval"]),
                score = (payload["score"] as? Number)?.toDouble(),
                breakdown = (payload["breakdown"] as? Map<*, *>)?.let {
                    ScoreBreakdown.fromMap(it.entries.associate { e -> e.key.toString() to e.value })
                },
                intent = (payload["intent"] as? Map<*, *>)?.let {
                    Intent(
                        capability = it["capability"]?.toString() ?: "",
                        args = (it["args"] as? Map<*, *>)?.entries?.associate { e ->
                            e.key.toString() to e.value
                        } ?: emptyMap(),
                    )
                },
                costOfWaiting = (payload["cost_of_waiting"] as? Number)?.toDouble() ?: 0.0,
                reversible = truthy(payload["reversible"]),
                undoHint = text("undo_hint"),
                traceId = text("trace_id") ?: "",
                deliver = payload["deliver"]?.let { truthy(it) } ?: true,
                record = payload["record"]?.let { truthy(it) } ?: true,
                createdAt = text("created_at"),
                confidenceSource = text("confidence_source") ?: "",
                calibrated = truthy(payload["calibrated"]),
                alternatives = list("alternatives").mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { e -> e.key.toString() to e.value }
                },
                constraintsApplied = list("constraints_applied").map { it.toString() },
                attributes = (payload["attributes"] as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: emptyMap(),
                target = TargetMode.from(text("target") ?: TargetMode.ONE.value),
                recipients = list("recipients").map { it.toString() },
                streamId = text("stream_id") ?: "",
                eventTime = text("event_time"),
                deadline = text("deadline"),
                validUntil = text("valid_until"),
                supersedes = text("supersedes"),
                revision = (payload["revision"] as? Number)?.toInt() ?: 0,
                status = DecisionStatus.from(text("status") ?: DecisionStatus.FINAL.value),
                schemaVersion = text("schema_version") ?: SCHEMA_VERSION,
            )
        }
    }
}
