package dev.laix.decision.appkit.streaming

import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.signals.parseIso
import java.time.Instant
import java.time.OffsetDateTime
import java.time.ZoneOffset
import kotlin.math.floor

/** One closed tumbling window. */
data class WindowBatch(
    val start: OffsetDateTime,
    val end: OffsetDateTime,
    val events: List<DecisionRequest>,
)

/** Group events by event time into fixed, non-overlapping windows. */
class TumblingWindow(
    val windowMs: Long,
    val late: String = "drop",
) {
    init {
        require(windowMs > 0) { "window_ms must be positive" }
        require(late in setOf("drop", "accept")) { "unknown late policy: '$late'" }
    }

    private var start: OffsetDateTime? = null
    private val events = mutableListOf<DecisionRequest>()
    private var watermark: OffsetDateTime? = null

    /** Add one event and return any window it closes. */
    fun add(event: DecisionRequest): List<WindowBatch> {
        val at = parseIso(event.at)
            ?: throw IllegalArgumentException("event has no valid at: '${event.at}'")

        val mark = watermark
        if (mark != null && at.toInstant() < mark.toInstant()) {
            if (late == "drop") return emptyList()
        } else {
            watermark = at
        }

        val windowStart = windowStart(at)
        val batches = mutableListOf<WindowBatch>()
        val current = start
        if (current == null) {
            start = windowStart
        } else if (windowStart.toInstant() > current.toInstant()) {
            batches += close()
            start = windowStart
        } else if (windowStart.toInstant() < current.toInstant() && late == "drop") {
            return emptyList()
        }

        events += event
        return batches
    }

    /** Close the current window, if it has events. */
    fun flush(): List<WindowBatch> {
        if (events.isEmpty()) return emptyList()
        return listOf(close())
    }

    val pending: Int
        get() = events.size

    private fun close(): WindowBatch {
        val windowStart = start ?: error("no window start")
        val batch = WindowBatch(
            start = windowStart,
            end = windowStart.plusNanos(windowMs * 1_000_000),
            events = events.toList(),
        )
        events.clear()
        return batch
    }

    private fun windowStart(at: OffsetDateTime): OffsetDateTime {
        val seconds = windowMs / 1000.0
        val epoch = at.toInstant().toEpochMilli() / 1000.0
        val startSeconds = floor(epoch / seconds) * seconds
        return Instant.ofEpochMilli((startSeconds * 1000).toLong()).atOffset(ZoneOffset.UTC)
    }
}
