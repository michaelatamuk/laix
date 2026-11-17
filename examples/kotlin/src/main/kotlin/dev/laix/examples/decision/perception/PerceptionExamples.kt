package dev.laix.examples.decision.perception

import dev.laix.decision.appkit.livecontext.LiveContext
import dev.laix.decision.perception.CallableDetector
import dev.laix.decision.perception.Detection
import dev.laix.decision.perception.PerceptionEvent
import dev.laix.decision.sensing.resources.Budget
import dev.laix.decision.sensing.resources.ResourceScheduler
import dev.laix.decision.sensing.resources.SensingOption
import dev.laix.examples.AT

/** Admit the sensor calls that fit the budget and buy enough information. */
fun resourceScheduler(): String {
    val plan = ResourceScheduler().schedule(
        options = listOf(
            SensingOption("cheap", tier = "cheap", cost = 0.1, latencyMs = 50, informationGain = 0.4),
            SensingOption("deep", tier = "deep", cost = 0.9, latencyMs = 600, informationGain = 0.9),
        ),
        budget = Budget(maxDeepCalls = 1, maxCost = 1.0, maxLatencyMs = 1_000),
        uncertainty = 0.8,
    )
    return "allowed=${plan.allowed} reason=${plan.reason} cost=${plan.cost} deep=${plan.deepCalls}"
}

/** Run detectors over an event and return one perception frame. */
fun liveContext(): String {
    val detector = CallableDetector(
        name = "leak",
        handler = { event ->
            listOf(
                Detection(
                    id = "det-1",
                    detector = "leak",
                    kind = "water",
                    subject = event.subject,
                    at = event.at,
                    confidence = 0.9,
                    severity = "high",
                ),
            )
        },
        tier = "cheap",
        cost = 0.1,
        latencyMs = 20,
        informationGain = 0.6,
    )
    val context = LiveContext(listOf(detector))
    val frame = context.perceive(
        PerceptionEvent(subject = "kitchen sink", at = AT, payload = mapOf("pressure" to 0.9)),
        uncertainty = 0.7,
    )
    return "detectors=${context.detectors()} detections=${frame.detections.size} " +
        "allowed=${frame.allowed} uncertainty=${frame.uncertainty}"
}
