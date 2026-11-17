package dev.laix.decision.appkit.audit

import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.support.iso
import dev.laix.decision.support.pythonFloatRepr
import dev.laix.decision.support.pythonJsonString
import java.security.MessageDigest

/** The approval state carried by a decision record. */
data class Approval(
    val required: Boolean,
    val state: String = "pending",
    val by: String? = null,
    val at: String? = null,
    val note: String? = null,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "required" to required,
            "state" to state,
            "by" to by,
            "at" to at,
            "note" to note,
        )
}

/** One append-only audit event on a decision record. */
data class AuditEvent(
    val at: String,
    val actor: String,
    val event: String,
    val detail: String = "",
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf("at" to at, "actor" to actor, "event" to event, "detail" to detail)
}

/** Whether a decision record can still be undone. */
data class Undo(
    val available: Boolean = false,
    val how: String? = null,
    val at: String? = null,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf("available" to available, "how" to how, "at" to at)
}

/** A storage-free decision record: what, why, evidence, approval, audit and undo. */
data class DecisionRecord(
    val id: String,
    val title: String,
    val summary: String,
    val decision: Map<String, Any?>,
    val evidence: List<EvidenceRef>,
    val approval: Approval,
    val status: String,
    val createdAt: String,
    val updatedAt: String,
    val audit: List<AuditEvent>,
    val undo: Undo,
    val metadata: Map<String, Any?>,
    val hash: String,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "version" to 1,
            "title" to title,
            "summary" to summary,
            "decision" to decision,
            "evidence" to evidence.map { it.toMap() },
            "approval" to approval.toMap(),
            "status" to status,
            "created_at" to createdAt,
            "updated_at" to updatedAt,
            "audit" to audit.map { it.toMap() },
            "undo" to undo.toMap(),
            "metadata" to metadata,
            "hash" to hash,
        )
}

private fun canonical(value: Any?): String =
    when (value) {
        null -> "null"
        is Boolean -> if (value) "true" else "false"
        is Number -> when (value) {
            is Int, is Long, is Short, is Byte -> value.toString()
            is Double -> pythonFloatRepr(value)
            is Float -> pythonFloatRepr(value.toDouble())
            else -> pythonFloatRepr(value.toDouble())
        }
        is String -> pythonJsonString(value)
        is Map<*, *> -> value.entries
            .sortedBy { it.key.toString() }
            .joinToString(separator = ",", prefix = "{", postfix = "}") {
                "${pythonJsonString(it.key.toString())}:${canonical(it.value)}"
            }
        is Iterable<*> -> value.joinToString(separator = ",", prefix = "[", postfix = "]") {
            canonical(it)
        }
        is Array<*> -> value.joinToString(separator = ",", prefix = "[", postfix = "]") {
            canonical(it)
        }
        else -> pythonJsonString(value.toString())
    }

private fun hash(payload: Map<String, Any?>): String {
    val digest = MessageDigest.getInstance("SHA-256")
        .digest(canonical(payload).toByteArray(Charsets.UTF_8))
    return "sha256:" + digest.joinToString("") { "%02x".format(it.toInt() and 0xFF) }
}

private fun seal(record: DecisionRecord): DecisionRecord {
    val payload = record.toMap() - "hash"
    return record.copy(hash = hash(payload))
}

private fun event(record: DecisionRecord, actor: String, event: String, detail: String): DecisionRecord {
    val at = iso()
    return record.copy(
        audit = record.audit + AuditEvent(at = at, actor = actor, event = event, detail = detail),
        updatedAt = at,
    )
}

fun createRecord(
    title: String,
    decision: String,
    evidence: List<EvidenceRef>,
    confidence: Double = 0.8,
    rationale: String = "",
    requiresApproval: Boolean = true,
    metadata: Map<String, Any?> = emptyMap(),
    recordId: String? = null,
    now: String? = null,
): DecisionRecord {
    require(title.isNotBlank() && decision.isNotBlank()) { "title and decision are required" }
    require(evidence.isNotEmpty()) { "at least one evidence ref is required" }
    val moment = now ?: iso()
    val id = recordId?.takeIf { it.isNotEmpty() } ?: (
        "dr-" + MessageDigest.getInstance("SHA-256")
            .digest("$title|$moment".toByteArray(Charsets.UTF_8))
            .joinToString("") { "%02x".format(it.toInt() and 0xFF) }
            .take(12)
        )
    val record = DecisionRecord(
        id = id,
        title = title.trim(),
        summary = decision.trim(),
        decision = linkedMapOf(
            "text" to decision.trim(),
            "confidence" to confidence.coerceIn(0.0, 1.0),
            "rationale" to rationale,
        ),
        evidence = evidence,
        approval = Approval(
            required = requiresApproval,
            state = if (requiresApproval) "pending" else "approved",
        ),
        status = if (requiresApproval) "draft" else "approved",
        createdAt = moment,
        updatedAt = moment,
        audit = listOf(AuditEvent(at = moment, actor = "agent", event = "created")),
        undo = Undo(),
        metadata = metadata,
        hash = "",
    )
    return seal(record)
}

fun approve(record: DecisionRecord, by: String, note: String = ""): DecisionRecord {
    require(record.status == "draft") { "cannot approve a ${record.status} record" }
    val stamped = event(record, by, "approved", note)
    val next = stamped.copy(
        approval = Approval(
            required = true,
            state = "approved",
            by = by,
            at = stamped.updatedAt,
            note = note,
        ),
        status = "approved",
        undo = Undo(available = true, how = "Undo before execution"),
    )
    return seal(next)
}

fun reject(record: DecisionRecord, by: String, note: String = ""): DecisionRecord {
    require(record.status == "draft") { "cannot reject a ${record.status} record" }
    val stamped = event(record, by, "rejected", note)
    val next = stamped.copy(
        approval = Approval(
            required = true,
            state = "rejected",
            by = by,
            at = stamped.updatedAt,
            note = note,
        ),
        status = "rejected",
    )
    return seal(next)
}

fun markExecuted(record: DecisionRecord, by: String, note: String = ""): DecisionRecord {
    require(record.status == "approved") { "cannot execute a ${record.status} record" }
    return seal(event(record, by, "executed", note).copy(status = "executed"))
}

fun undo(record: DecisionRecord, by: String, note: String = ""): DecisionRecord {
    require(record.status in setOf("approved", "executed") && record.undo.available) {
        "this record is not undoable"
    }
    val next = event(record, by, "undone", note)
    return seal(
        next.copy(
            status = "undone",
            undo = Undo(available = false, how = record.undo.how, at = next.updatedAt),
        ),
    )
}

fun verify(record: DecisionRecord): Boolean =
    hash(record.toMap() - "hash") == record.hash
