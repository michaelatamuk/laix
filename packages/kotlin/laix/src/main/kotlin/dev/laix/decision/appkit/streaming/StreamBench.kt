package dev.laix.decision.appkit.streaming

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.support.round

/** Render the counters in Prometheus text format; no extra dependency. */
fun prometheus(stats: StreamStats, prefix: String = "laix_stream"): String {
    val lines = mutableListOf<String>()
    for ((key, value) in stats.snapshot()) {
        val name = "${prefix}_$key"
        lines += "# TYPE $name gauge"
        lines += "$name $value"
    }
    return lines.joinToString("\n") + "\n"
}

/** The outcome of replaying a stream bench. */
data class StreamBenchResult(
    val decisions: List<Decision>,
    val elapsedMs: Double,
    val throughputPerSecond: Double,
    val stats: Map<String, Any?>,
)

/** Replay requests through the session and report time and counters. */
fun runStreamBench(
    session: StreamSession,
    requests: List<DecisionRequest>,
): StreamBenchResult {
    val started = System.nanoTime()
    val decisions = session.replay(requests)
    val elapsedMs = (System.nanoTime() - started) / 1_000_000.0
    val throughput = if (elapsedMs > 0) decisions.size / (elapsedMs / 1000.0) else 0.0
    return StreamBenchResult(
        decisions = decisions,
        elapsedMs = round(elapsedMs, 3),
        throughputPerSecond = round(throughput, 3),
        stats = session.stats().snapshot(),
    )
}
