package dev.laix.decision.appkit

import dev.laix.decision.appkit.streaming.DeadLetterQueue
import dev.laix.decision.appkit.streaming.DecisionTimeline
import dev.laix.decision.appkit.streaming.ManualClock
import dev.laix.decision.appkit.streaming.StreamSession
import dev.laix.decision.appkit.streaming.TimelineError
import dev.laix.decision.appkit.streaming.TumblingWindow
import dev.laix.decision.appkit.streaming.fromNdjson
import dev.laix.decision.appkit.streaming.fromSse
import dev.laix.decision.appkit.streaming.prometheus
import dev.laix.decision.appkit.streaming.runStreamBench
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import java.time.OffsetDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class StreamingExtrasTest {
    private val at = "2026-11-01T10:00:00+00:00"

    private fun request(atValue: String = at) = DecisionRequest(
        subject = "room-1",
        at = atValue,
        options = listOf(ActionOption("a-1", Verb.WAIT, "wait")),
    )

    private fun decision(
        id: String = "",
        revision: Int = 0,
        supersedes: String? = null,
        eventTime: String? = null,
        streamId: String = "",
    ) = Decision(
        verb = Verb.WAIT,
        confidence = 0.5,
        reasonCode = "policy_rule",
        rationale = "wait",
        decisionId = id,
        revision = revision,
        supersedes = supersedes,
        eventTime = eventTime,
        streamId = streamId,
    )

    @Test
    fun `refined decisions add a revision`() = runBlocking {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )

        val result = session.observeRefined(request(), refine = { listOf(decision()) })

        assertEquals(2, result.size)
        assertEquals(1, result[1].revision)
        assertEquals(result[0].decisionId, result[1].supersedes)
    }

    @Test
    fun `refinement timeouts fall back to final`() = runBlocking {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )

        val result = session.observeRefined(
            request(),
            refine = {
                delay(2_000)
                listOf(decision())
            },
            timeoutMs = 20,
        )

        assertEquals(2, result.size)
        assertEquals(1, session.stats().refineTimeouts)
    }

    @Test
    fun `feed consumes a flow`() = runBlocking {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )

        val decisions = session.feed(
            flowOf(
                request("2026-11-01T10:00:00+00:00"),
                request("2026-11-01T10:01:00+00:00"),
            ),
        ).toList()

        assertEquals(2, decisions.size)
    }

    @Test
    fun `windows are decided when they close`() = runBlocking {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )

        val decisions = session.feedWindows(
            flowOf(
                request("2026-11-01T10:00:10+00:00"),
                request("2026-11-01T10:00:20+00:00"),
                request("2026-11-01T10:01:10+00:00"),
            ),
            windowMs = 60_000,
            onWindow = { request("2026-11-01T10:00:00+00:00") },
        ).toList()

        assertEquals(2, decisions.size)
    }

    @Test
    fun `decisions drains the buffer and closes`() = runBlocking {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )
        session.observe(request())
        session.close()

        assertEquals(1, session.decisions().toList().size)
    }

    @Test
    fun `tumbling windows close on the next window`() {
        val window = TumblingWindow(windowMs = 60_000)
        window.add(request("2026-11-01T10:00:30+00:00"))
        window.add(request("2026-11-01T10:00:45+00:00"))
        assertEquals(2, window.pending)

        val closed = window.add(request("2026-11-01T10:01:20+00:00"))

        assertEquals(1, closed.size)
        assertEquals("2026-11-01T10:00:00Z", closed.first().start.toInstant().toString())
        assertEquals(2, closed.first().events.size)
        assertEquals(1, window.pending)

        val flushed = window.flush()
        assertEquals(1, flushed.size)
        assertEquals(1, flushed.first().events.size)
        assertEquals(emptyList(), window.flush())
    }

    @Test
    fun `tumbling windows drop late events`() {
        val window = TumblingWindow(windowMs = 60_000)
        window.add(request("2026-11-01T10:01:00+00:00"))

        assertEquals(emptyList(), window.add(request("2026-11-01T09:59:00+00:00")))
        assertEquals(1, window.pending)
    }

    @Test
    fun `windows validate their settings`() {
        assertFailsWith<IllegalArgumentException> { TumblingWindow(0) }
        assertFailsWith<IllegalArgumentException> { TumblingWindow(1000, late = "keep") }
        assertFailsWith<IllegalArgumentException> {
            TumblingWindow(1000).add(request("not-a-time"))
        }
    }

    @Test
    fun `timelines enforce revision rules`() {
        val timeline = DecisionTimeline()
        timeline.add(decision("d1", revision = 0, eventTime = "2026-11-01T10:00:00+00:00", streamId = "s"))
        timeline.add(
            decision(
                "d2",
                revision = 1,
                supersedes = "d1",
                eventTime = "2026-11-01T10:01:00+00:00",
                streamId = "s",
            ),
        )

        assertEquals(listOf("d1", "d2"), timeline.all().map { it.decisionId })
        assertEquals(listOf("d1", "d2"), timeline.history("d2").map { it.decisionId })
        assertEquals(setOf("d1"), timeline.supersededIds())
        assertEquals(listOf("d2"), timeline.current().map { it.decisionId })
        assertEquals("d2", timeline.latest()?.decisionId)
        assertEquals(1, timeline.late("2026-11-01T10:00:30+00:00").size)
        val report = timeline.report()
        assertEquals(2, report.decisions)
        assertEquals(1, report.chains)
        assertEquals(1, report.superseded)
        assertTrue(report.valid)

        assertFailsWith<TimelineError> { timeline.add(decision("d1")) }
        assertFailsWith<TimelineError> {
            timeline.add(decision("d3", revision = 0, supersedes = "d1"))
        }
        assertFailsWith<TimelineError> {
            timeline.add(
                decision("d4", revision = 3, supersedes = "d2", eventTime = "2026-11-01T10:02:00+00:00"),
            )
        }
        assertFailsWith<TimelineError> {
            timeline.add(
                decision(
                    "d5",
                    revision = 2,
                    supersedes = "d2",
                    eventTime = "2026-11-01T09:00:00+00:00",
                ),
            )
        }
        assertFailsWith<TimelineError> { timeline.get("missing") }
    }

    @Test
    fun `timelines round-trip`() {
        val source = DecisionTimeline(
            listOf(decision("d1", revision = 0, eventTime = "2026-11-01T10:00:00+00:00")),
        )

        val restored = DecisionTimeline.fromMap(source.toMap())

        assertEquals(source.all().map { it.decisionId }, restored.all().map { it.decisionId })
    }

    @Test
    fun `NDJSON and SSE sources parse requests`() {
        val line = """{"subject":"room-1","at":"$at","signals":[]}"""
        assertEquals(1, fromNdjson(listOf(line, "")).size)

        val dead = DeadLetterQueue(limit = 2)
        val parsed = fromNdjson(listOf(line, "not-json", "{}"), onError = dead.asErrorHandler(), strict = false)
        assertEquals(1, parsed.size)
        assertEquals(2, dead.size)
        assertTrue(dead.all().first().error.isNotEmpty())
        assertFailsWith<Exception> { fromNdjson(listOf("not-json")) }

        val sse = fromSse(
            listOf("data: $line", "", "event: ignored", "data: $line", ""),
        )
        assertEquals(2, sse.size)
    }

    @Test
    fun `the stream bench reports time and counters`() {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )

        val result = runStreamBench(
            session,
            listOf(request("2026-11-01T10:00:00+00:00"), request("2026-11-01T10:01:00+00:00")),
        )

        assertEquals(2, result.decisions.size)
        assertEquals(2, result.stats["decided"])
        assertTrue(result.throughputPerSecond >= 0.0)
        val text = prometheus(session.stats())
        assertTrue(text.contains("# TYPE laix_stream_observed gauge"))
        assertTrue(text.contains("laix_stream_decided 2"))
    }

    @Test
    fun `stream sessions can keep a timeline and checkpoint it`() {
        val manual = ManualClock(OffsetDateTime.parse(at))
        val timeline = DecisionTimeline()
        val session = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
            timeline = timeline,
        )
        val first = session.observe(request()).single()
        manual.set(OffsetDateTime.parse("2026-11-01T10:01:00+00:00"))
        session.revise(first, request("2026-11-01T10:01:00+00:00"))

        assertEquals(2, timeline.all().size)
        assertEquals(1, timeline.current().size)
        val snapshot = session.snapshot()
        assertTrue(snapshot["timeline"] is Map<*, *>)

        val restored = StreamSession(
            decide = { request -> listOf(decision(eventTime = request.at)) },
            clock = { manual() },
        )
        restored.restore(snapshot)
        assertEquals(2, restored.timeline?.all()?.size)
    }
}
