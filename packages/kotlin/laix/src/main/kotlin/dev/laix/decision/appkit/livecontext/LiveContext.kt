package dev.laix.decision.appkit.livecontext

import dev.laix.decision.perception.Detection
import dev.laix.decision.perception.Detector
import dev.laix.decision.perception.PerceptionEvent
import dev.laix.decision.perception.PerceptionFrame
import dev.laix.decision.sensing.resources.Budget
import dev.laix.decision.sensing.resources.ResourceScheduler
import dev.laix.decision.sensing.resources.SensingOption
import dev.laix.decision.support.clamp

/** Run detectors over an event stream and return perception frames. */
class LiveContext(
    detectors: List<Detector> = emptyList(),
    val budget: Budget = Budget(maxDeepCalls = 2, maxCost = 1.0, maxLatencyMs = 500),
    val policy: ResourceScheduler = ResourceScheduler(),
) {
    private val registered = LinkedHashMap<String, Detector>()
    val frames: MutableList<PerceptionFrame> = mutableListOf()

    init {
        detectors.forEach { register(it) }
    }

    fun register(detector: Detector) {
        val name = detector.name.trim()
        require(name.isNotEmpty()) { "detector name is required" }
        registered[name] = detector
    }

    fun detectors(): List<String> = registered.keys.toList()

    fun perceive(event: PerceptionEvent, uncertainty: Double = 0.5): PerceptionFrame {
        val clamped = clamp(uncertainty)
        val options = registered.values.map {
            SensingOption(
                name = it.name,
                tier = it.tier,
                cost = it.cost,
                latencyMs = it.latencyMs,
                informationGain = it.informationGain,
            )
        }
        val plan = policy.schedule(options, budget, clamped)

        val detections = mutableListOf<Detection>()
        var remaining = clamped
        for (name in plan.allowed) {
            val detector = registered[name] ?: continue
            val found = detector.detect(event)
            detections += found
            if (found.isNotEmpty()) {
                val best = found.maxOf { it.confidence }
                val gain = detector.informationGain * best
                remaining *= 1.0 - minOf(0.98, gain)
            }
        }

        val frame = PerceptionFrame(
            subject = event.subject,
            at = event.at,
            detections = detections,
            allowed = plan.allowed,
            skipped = plan.skipped,
            uncertainty = clamp(remaining),
            deepCalls = plan.deepCalls,
            cost = plan.cost,
        )
        frames += frame
        return frame
    }

    fun feed(events: List<PerceptionEvent>, uncertainty: Double = 0.5): List<PerceptionFrame> =
        events.map { perceive(it, uncertainty) }

    val latest: PerceptionFrame?
        get() = frames.lastOrNull()
}
