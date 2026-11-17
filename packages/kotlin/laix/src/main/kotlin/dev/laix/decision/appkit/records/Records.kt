package dev.laix.decision.appkit.records

import dev.laix.decision.contracts.SCHEMA_VERSION
import dev.laix.decision.support.iso
import dev.laix.decision.support.toJson

/** Ordered evidence for one decision: input, policy, execution, outcome. */
data class Trace(
    val id: String,
    val decisionId: String,
    val createdAt: String = iso(),
    val events: List<Map<String, Any?>> = emptyList(),
    val schemaVersion: String = SCHEMA_VERSION,
) {
    fun withEvent(
        stage: String,
        detail: Map<String, Any?> = emptyMap(),
        at: String? = null,
    ): Trace =
        copy(
            events = events + linkedMapOf(
                "at" to (at ?: iso()),
                "stage" to stage,
                "detail" to detail,
            ),
        )

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "decision_id" to decisionId,
            "created_at" to createdAt,
            "events" to events,
            "schema_version" to schemaVersion,
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)
}

val EXECUTION_RECEIPT_STATUSES: List<String> = listOf(
    "pending",
    "approved",
    "executed",
    "refused",
    "cancelled",
    "failed",
    "undone",
    "unknown",
    "duplicate",
)

/** Proof that an action was executed, refused, cancelled or undone. */
data class ExecutionReceipt(
    val id: String,
    val decisionId: String,
    val actionName: String,
    val status: String,
    val actor: String,
    val at: String = iso(),
    val detail: Map<String, Any?> = emptyMap(),
    val previousState: Map<String, Any?>? = null,
    val error: String? = null,
    val approvedBy: String? = null,
    val idempotencyKey: String? = null,
    val schemaVersion: String = SCHEMA_VERSION,
) {
    init {
        require(status in EXECUTION_RECEIPT_STATUSES) { "unknown receipt status: $status" }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "decision_id" to decisionId,
            "action_name" to actionName,
            "status" to status,
            "actor" to actor,
            "at" to at,
            "detail" to detail,
            "previous_state" to previousState,
            "error" to error,
            "approved_by" to approvedBy,
            "idempotency_key" to idempotencyKey,
            "schema_version" to schemaVersion,
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)
}
