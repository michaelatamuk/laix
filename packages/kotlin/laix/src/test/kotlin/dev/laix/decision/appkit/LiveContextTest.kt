package dev.laix.decision.appkit

import dev.laix.decision.appkit.livecontext.LiveContext
import dev.laix.decision.perception.CallableDetector
import dev.laix.decision.perception.Detection
import dev.laix.decision.perception.PerceptionEvent
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class LiveContextTest {
    private val event = PerceptionEvent(
        subject = "room-1",
        at = "2026-11-01T10:00:00+00:00",
        payload = mapOf("temperature" to 30),
    )

    private fun detection(id: String, confidence: Double) = Detection(
        id = id,
        detector = "cheap",
        kind = "reading",
        subject = event.subject,
        at = event.at,
        confidence = confidence,
    )

    @Test
    fun `cheap detectors run continuously`() {
        val context = LiveContext(
            listOf(
                CallableDetector(
                    name = "cheap",
                    handler = { listOf(detection("d-1", 0.5)) },
                ),
            ),
        )

        val frame = context.perceive(event, uncertainty = 0.2)

        assertEquals(listOf("cheap"), frame.allowed)
        assertEquals(1, frame.detections.size)
        assertEquals(listOf(frame), context.frames)
        assertEquals(frame, context.latest)
        assertEquals(0, frame.deepCalls)
    }

    @Test
    fun `deep detectors need information gain`() {
        val context = LiveContext(
            listOf(
                CallableDetector(
                    name = "deep",
                    handler = { listOf(detection("d-1", 0.9)) },
                    tier = "deep",
                    informationGain = 0.9,
                ),
            ),
        )

        val skipped = context.perceive(event, uncertainty = 0.2)
        assertEquals(emptyList(), skipped.allowed)
        assertTrue(skipped.skipped.single()["reason"].toString().contains("below threshold"))

        val admitted = context.perceive(event, uncertainty = 0.9)
        assertEquals(listOf("deep"), admitted.allowed)
        assertEquals(1, admitted.deepCalls)
        assertTrue(admitted.uncertainty < 0.9)
    }

    @Test
    fun `frames capture budget and detectors`() {
        val context = LiveContext(
            detectors = listOf(
                CallableDetector("cheap", { listOf(detection("d-1", 0.5)) }),
                CallableDetector(
                    "deep",
                    { listOf(detection("d-2", 0.9)) },
                    tier = "deep",
                    informationGain = 0.9,
                ),
            ),
        )

        assertEquals(listOf("cheap", "deep"), context.detectors())
        val frames = context.feed(listOf(event, event.copy(at = "2026-11-01T10:01:00+00:00")))
        assertEquals(2, frames.size)
        assertEquals(2, context.frames.size)
        assertNotNull(context.latest)

        val payload = context.latest!!.toMap()
        assertEquals("room-1", payload["subject"])
        assertEquals(2, (payload["detections"] as List<*>).size)
    }

    @Test
    fun `detector names are required and detections clamp`() {
        assertFailsWith<IllegalArgumentException> {
            LiveContext(listOf(CallableDetector("  ", { emptyList() })))
        }
        assertEquals(1.0, detection("d", 2.0).confidence)
        assertEquals(0.0, detection("d", -1.0).confidence)
    }
}
