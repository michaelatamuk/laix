package dev.laix.examples.appkit.run

import dev.laix.decision.appkit.streaming.DecisionTimeline
import dev.laix.decision.appkit.streaming.InMemoryStreamCheckpointStore
import dev.laix.decision.appkit.streaming.StreamSession
import dev.laix.decision.appkit.streaming.TumblingWindow
import dev.laix.decision.appkit.streaming.WindowBatch
import dev.laix.decision.appkit.streaming.fromNdjson
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.decide
import dev.laix.examples.AT
import dev.laix.examples.paymentOptions
import dev.laix.examples.paymentSituation
import dev.laix.examples.sinkOptions
import dev.laix.examples.sinkSituation
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking

private fun sinkRequest(atValue: String = AT): DecisionRequest =
    DecisionRequest(subject = "kitchen sink", at = atValue, situation = sinkSituation(), options = sinkOptions())

private fun paymentRequest(atValue: String): DecisionRequest =
    DecisionRequest(subject = "electricity bill", at = atValue, situation = paymentSituation(), options = paymentOptions())

/** Admit events into one stream and drain the buffered decisions. */
fun streamSession(): String {
    val session = StreamSession(decide = { request -> decide(request) }, streamId = "stream-1")
    session.observe(sinkRequest())
    session.observe(paymentRequest("2026-11-01T10:01:00+00:00"))
    val drained = session.drain()
    return "drained=${drained.size} verbs=${drained.map { it.verb.value }} " +
        "decided=${session.stats().decided} pending=${session.pending}"
}

/** Save a stream snapshot and resume it in a new session. */
fun streamCheckpoint(): String {
    val session = StreamSession(decide = { request -> decide(request) }, streamId = "stream-1", capacity = 4)
    session.observe(sinkRequest())
    val store = InMemoryStreamCheckpointStore()
    session.save(store, "room-1")

    val resumed = StreamSession(decide = { request -> decide(request) }, streamId = "stream-1")
    val found = resumed.resume(store, "room-1")
    return "found=$found stream=${resumed.streamId} pending=${resumed.pending}"
}

/** Feed a flow of requests; the session returns the same decision shape. */
fun streamFeed(): String = runBlocking {
    val session = StreamSession(decide = { request -> decide(request) })
    val decisions = session.feed(
        flowOf(sinkRequest(), paymentRequest("2026-11-01T10:01:00+00:00")),
    ).toList()
    "decisions=${decisions.size} verbs=${decisions.map { it.verb.value }}"
}

/** Aggregate events into tumbling windows before deciding. */
fun tumblingWindow(): String {
    val window = TumblingWindow(windowMs = 60_000)
    val batches = mutableListOf<WindowBatch>()
    batches += window.add(sinkRequest("2026-11-01T10:00:05+00:00"))
    batches += window.add(paymentRequest("2026-11-01T10:01:10+00:00"))
    batches += window.flush()
    return "batches=${batches.size} sizes=${batches.map { it.events.size }}"
}

/** Read one request per JSON line. */
fun ndjsonSource(): String {
    val requests = fromNdjson(
        listOf(
            """{"subject":"room-1","at":"2026-11-01T10:00:00+00:00","options":[{"id":"a-1","verb":"wait","name":"wait"}]}""",
            """{"subject":"room-2","at":"2026-11-01T10:01:00+00:00","options":[{"id":"a-2","verb":"act","name":"act"}]}""",
        ),
    )
    return "requests=${requests.size} subjects=${requests.map { it.subject }}"
}

/** Keep a decision timeline and check which decisions are still current. */
fun decisionTimeline(): String {
    val timeline = DecisionTimeline()
    val first = Decision(
        verb = Verb.WAIT,
        confidence = 0.6,
        reasonCode = "first",
        rationale = "wait",
        decisionId = "DEC-1",
        streamId = "stream-1",
        revision = 0,
    )
    val second = first.copy(
        decisionId = "DEC-2",
        reasonCode = "second",
        rationale = "act",
        verb = Verb.ACT,
        revision = 1,
        supersedes = "DEC-1",
    )
    timeline.add(first)
    timeline.add(second)
    return "current=${timeline.current().map { it.decisionId }} " +
        "superseded=${timeline.supersededIds()} valid=${timeline.report().valid}"
}
