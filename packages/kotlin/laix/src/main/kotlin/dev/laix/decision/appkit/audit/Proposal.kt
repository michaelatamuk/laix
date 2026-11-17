package dev.laix.decision.appkit.audit

import dev.laix.decision.support.iso

val PROPOSAL_STATUSES: List<String> = listOf(
    "pending",
    "approved",
    "rejected",
    "applied",
    "undone",
)

/** A small, storage-free proposal and approval record. */
data class Proposal(
    val id: String,
    val title: String,
    val summary: String,
    val decisionId: String = "",
    val actionId: String? = null,
    val status: String = "pending",
    val createdAt: String = iso(),
    val createdBy: String = "agent",
    val approvedBy: String? = null,
    val approvedAt: String? = null,
    val appliedAt: String? = null,
    val undoHint: String? = null,
    val payload: Map<String, Any?> = emptyMap(),
) {
    init {
        require(status in PROPOSAL_STATUSES) { "unknown proposal status: '$status'" }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "title" to title,
            "summary" to summary,
            "decision_id" to decisionId,
            "action_id" to actionId,
            "status" to status,
            "created_at" to createdAt,
            "created_by" to createdBy,
            "approved_by" to approvedBy,
            "approved_at" to approvedAt,
            "applied_at" to appliedAt,
            "undo_hint" to undoHint,
            "payload" to payload,
        )
}

fun approve(proposal: Proposal, by: String, at: String? = null): Proposal {
    require(proposal.status == "pending") {
        "cannot approve a ${proposal.status} proposal"
    }
    return proposal.copy(
        status = "approved",
        approvedBy = by,
        approvedAt = at ?: iso(),
    )
}

fun reject(proposal: Proposal, by: String, at: String? = null): Proposal {
    require(proposal.status == "pending") {
        "cannot reject a ${proposal.status} proposal"
    }
    return proposal.copy(
        status = "rejected",
        approvedBy = by,
        approvedAt = at ?: iso(),
    )
}

fun apply(proposal: Proposal, at: String? = null): Proposal {
    require(proposal.status == "approved") {
        "cannot apply a ${proposal.status} proposal"
    }
    return proposal.copy(status = "applied", appliedAt = at ?: iso())
}

fun undo(proposal: Proposal, at: String? = null): Proposal {
    require(proposal.status == "applied") {
        "cannot undo a ${proposal.status} proposal"
    }
    return proposal.copy(status = "undone", appliedAt = at ?: iso())
}
