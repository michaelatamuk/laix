package dev.laix.decision.appkit.delivery

import dev.laix.decision.contracts.Decision
import dev.laix.decision.support.iso

val DELIVERY_STATUSES: List<String> = listOf("delivered", "skipped", "failed")

/** The receipt an app can persist after trying to deliver a decision. */
data class DeliveryReceipt(
    val id: String,
    val decisionId: String,
    val channel: String,
    val status: String,
    val at: String = iso(),
    val detail: Map<String, Any?> = emptyMap(),
) {
    init {
        require(status in DELIVERY_STATUSES) { "unknown delivery status: '$status'" }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "decision_id" to decisionId,
            "channel" to channel,
            "status" to status,
            "at" to at,
            "detail" to detail,
        )
}

/** An app-supplied transport. */
interface DeliveryPort {
    fun deliver(decision: Decision, message: Any?, channel: String = "default"): DeliveryReceipt
}

/** A delivery port that records receipts in memory and delivers nothing. */
class NullDelivery(
    receipts: List<DeliveryReceipt> = emptyList(),
) : DeliveryPort {
    var receipts: List<DeliveryReceipt> = receipts.toList()
        private set

    override fun deliver(decision: Decision, message: Any?, channel: String): DeliveryReceipt {
        val receipt = DeliveryReceipt(
            id = "dl-${receipts.size + 1}",
            decisionId = decision.decisionId,
            channel = channel,
            status = "skipped",
            detail = mapOf("message" to message),
        )
        receipts = receipts + receipt
        return receipt
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf("receipts" to receipts.map { it.toMap() })
}
