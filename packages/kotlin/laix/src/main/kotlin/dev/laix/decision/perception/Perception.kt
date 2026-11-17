package dev.laix.decision.perception

import dev.laix.decision.support.clamp
import dev.laix.decision.support.round

/** One input to the loop: what happened, when and where. */
data class PerceptionEvent(
    val subject: String,
    val at: String,
    val payload: Map<String, Any?> = emptyMap(),
)

/** One thing a detector noticed in one event. */
@ConsistentCopyVisibility
data class Detection private constructor(
    val id: String,
    val detector: String,
    val kind: String,
    val subject: String,
    val at: String,
    val confidence: Double,
    val severity: String,
    val payload: Map<String, Any?>,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "detector" to detector,
            "kind" to kind,
            "subject" to subject,
            "at" to at,
            "confidence" to confidence,
            "severity" to severity,
            "payload" to payload,
        )

    companion object {
        operator fun invoke(
            id: String,
            detector: String,
            kind: String,
            subject: String,
            at: String,
            confidence: Double = 0.5,
            severity: String = "low",
            payload: Map<String, Any?> = emptyMap(),
        ): Detection = create(id, detector, kind, subject, at, clamp(confidence), severity, payload)

        private fun create(
            id: String,
            detector: String,
            kind: String,
            subject: String,
            at: String,
            confidence: Double,
            severity: String,
            payload: Map<String, Any?>,
        ): Detection = Detection(id, detector, kind, subject, at, confidence, severity, payload)
    }
}

/** A cheap or deep detector the app supplies. */
interface Detector {
    val name: String
    val tier: String
    val cost: Double
    val latencyMs: Int
    val informationGain: Double

    fun detect(event: PerceptionEvent): List<Detection>
}

/** A detector built from a plain function. */
class CallableDetector(
    override val name: String,
    private val handler: (PerceptionEvent) -> List<Detection>,
    override val tier: String = "cheap",
    override val cost: Double = 0.0,
    override val latencyMs: Int = 0,
    override val informationGain: Double = 0.0,
) : Detector {
    override fun detect(event: PerceptionEvent): List<Detection> = handler(event)
}

/** What the loop saw for one event and what it skipped. */
data class PerceptionFrame(
    val subject: String,
    val at: String,
    val detections: List<Detection>,
    val allowed: List<String>,
    val skipped: List<Map<String, Any?>>,
    val uncertainty: Double,
    val deepCalls: Int = 0,
    val cost: Double = 0.0,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "subject" to subject,
            "at" to at,
            "detections" to detections.map { it.toMap() },
            "allowed" to allowed,
            "skipped" to skipped,
            "uncertainty" to round(uncertainty, 6),
            "deepCalls" to deepCalls,
            "cost" to round(cost, 6),
        )
}
