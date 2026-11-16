package dev.laix.decision.contracts

/** A reference to the evidence behind a decision. */
data class EvidenceRef(
    val id: String,
    val kind: String = "reference",
    val quote: String? = null,
    val source: String? = null,
    val confidence: Double? = null,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "kind" to kind,
            "quote" to quote,
            "source" to source,
            "confidence" to confidence,
        )

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): EvidenceRef =
            EvidenceRef(
                id = payload["id"]?.toString() ?: "",
                kind = payload["kind"]?.toString() ?: "reference",
                quote = payload["quote"]?.toString(),
                source = payload["source"]?.toString(),
                confidence = (payload["confidence"] as? Number)?.toDouble(),
            )
    }
}

/** The inspectable score breakdown behind a signal-attention decision. */
data class ScoreBreakdown(
    val severity: Double = 0.0,
    val due: Double = 0.0,
    val confidence: Double = 0.0,
    val interruption: Double = 0.0,
    val learned: Double = 0.0,
    val total: Double = 0.0,
) {
    fun asDict(): Map<String, Double> =
        linkedMapOf(
            "severity" to round2(severity),
            "due" to round2(due),
            "confidence" to round2(confidence),
            "interruption" to round2(interruption),
            "learned" to round2(learned),
            "total" to round2(total),
        )

    fun toMap(): Map<String, Any?> = linkedMapOf(
        "severity" to severity,
        "due" to due,
        "confidence" to confidence,
        "interruption" to interruption,
        "learned" to learned,
        "total" to total,
    )

    companion object {
        fun fromMap(payload: Map<String, Any?>): ScoreBreakdown =
            ScoreBreakdown(
                severity = (payload["severity"] as? Number)?.toDouble() ?: 0.0,
                due = (payload["due"] as? Number)?.toDouble() ?: 0.0,
                confidence = (payload["confidence"] as? Number)?.toDouble() ?: 0.0,
                interruption = (payload["interruption"] as? Number)?.toDouble() ?: 0.0,
                learned = (payload["learned"] as? Number)?.toDouble() ?: 0.0,
                total = (payload["total"] as? Number)?.toDouble() ?: 0.0,
            )
    }
}

private fun round2(value: Double): Double =
    Math.round(value * 100.0) / 100.0
