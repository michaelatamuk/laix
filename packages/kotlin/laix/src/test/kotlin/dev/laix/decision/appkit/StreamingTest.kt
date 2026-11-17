package dev.laix.decision.appkit

import dev.laix.decision.appkit.streaming.InMemoryStreamCheckpointStore
import dev.laix.decision.appkit.streaming.ManualClock
import dev.laix.decision.appkit.streaming.StreamSession
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.DecisionStatus
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionBudget
import java.time.OffsetDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class StreamingTest {
    private val at = "2026-11-01T10:00:00+00:00"

    private fun request(
        atValue: String = at,
        eventId: String = "",
        deadline: String? = null,
    ) = DecisionRequest(
        subject = "room-1",
        at = atValue,
        options = listOf(ActionOption("a-1", Verb.WAIT, "wait")),
        eventId = eventId,
        deadline = deadline,
    )

    private fun decider(): (DecisionRequest) -> List<Decision> = { request ->
        listOf(
            Decision(
                verb = Verb.WAIT,
                confidence = 0.5,
                reasonCode = "policy_rule",
                rationale = "wait",
                actionId = request.options.firstOrNull()?.id,
            ),
        )
    }

    private fun clock(): ManualClock = ManualClock(OffsetDateTime.parse(at))

    @Test
    fun `observe stamps the stream and buffers the decision`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })

        val decisions = session.observe(request())
        val decision = decisions.single()

        assertTrue(session.streamId.startsWith("STR-"))
        assertEquals(session.streamId, decision.streamId)
        assertEquals(at, decision.eventTime)
        assertEquals(DecisionStatus.FINAL, decision.status)
        assertTrue(decision.decisionId.isNotEmpty())
        assertTrue(decision.traceId.isNotEmpty())
        assertEquals(1, session.stats().observed)
        assertEquals(1, session.stats().decided)
        assertEquals(1, session.pending)
        assertEquals(listOf(decision), session.drain())
        assertEquals(0, session.pending)
        assertTrue(session.trace(decision.decisionId).events.isNotEmpty())
    }

    @Test
    fun `late events are dropped by default`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })
        session.observe(request("2026-11-01T10:00:00+00:00"))

        val late = session.observe(request("2026-11-01T09:00:00+00:00"))

        assertEquals(emptyList(), late)
        assertEquals(1, session.stats().late)
    }

    @Test
    fun `cooldown and hysteresis suppress decisions`() {
        val manual = clock()
        val session = StreamSession(decider(), cooldownMs = 5000, clock = { manual() })
        session.observe(request())
        assertEquals(0, session.observe(request()).size)
        assertEquals(1, session.stats().throttled)

        val hysteresis = StreamSession(decider(), hysteresisMs = 10_000, clock = { manual() })
        assertEquals(1, hysteresis.observe(request()).size)
        assertEquals(0, hysteresis.observe(request()).size)
        assertEquals(1, hysteresis.stats().suppressed)
    }

    @Test
    fun `dedupe drops repeated event ids`() {
        val manual = clock()
        val session = StreamSession(decider(), dedupeMs = 60_000, clock = { manual() })
        assertEquals(1, session.observe(request(eventId = "e-1")).size)
        assertEquals(0, session.observe(request(eventId = "e-1")).size)
        assertEquals(1, session.stats().duplicates)
    }

    @Test
    fun `revisions supersede the previous decision`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })
        val first = session.observe(request()).single()
        manual.set(OffsetDateTime.parse("2026-11-01T10:01:00+00:00"))

        val revised = session.revise(first, request("2026-11-01T10:01:00+00:00")).single()

        assertEquals(first.decisionId, revised.supersedes)
        assertEquals(1, revised.revision)
        assertEquals(1, session.stats().revised)
    }

    @Test
    fun `a passed deadline makes the decision provisional`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })

        val decision = session.observe(
            request(deadline = "2026-11-01T09:00:00+00:00"),
        ).single()

        assertEquals(DecisionStatus.PROVISIONAL, decision.status)
        assertEquals(1, session.stats().provisional)
        assertEquals(1, session.stats().expired)
    }

    @Test
    fun `the decision budget sheds events`() {
        val manual = clock()
        val session = StreamSession(
            decider(),
            maxDecisionsPerWindow = 1,
            clock = { manual() },
        )

        assertEquals(1, session.observe(request()).size)
        assertEquals(0, session.observe(request()).size)
        assertEquals(1, session.stats().shed)
    }

    @Test
    fun `the buffer applies its overflow policy`() {
        val manual = clock()
        val session = StreamSession(
            decider(),
            capacity = 1,
            onFull = "drop_newest",
            clock = { manual() },
        )

        session.observe(request("2026-11-01T10:00:00+00:00"))
        session.observe(request("2026-11-01T10:01:00+00:00"))

        assertEquals(1, session.pending)
        assertEquals(1, session.stats().dropped)

        val latest = StreamSession(
            decider(),
            capacity = 1,
            onFull = "latest_wins",
            clock = { manual() },
        )
        latest.observe(request("2026-11-01T10:00:00+00:00"))
        latest.observe(request("2026-11-01T10:01:00+00:00"))
        assertEquals(1, latest.pending)
        assertEquals("2026-11-01T10:01:00+00:00", latest.drain().single().eventTime)
    }

    @Test
    fun `replay follows event time`() {
        val session = StreamSession(decider())

        val decisions = session.replay(
            listOf(
                request("2026-11-01T10:00:00+00:00"),
                request("2026-11-01T11:00:00+00:00"),
                request("2026-11-01T10:30:00+00:00"),
            ),
        )

        assertEquals(2, decisions.size)
    }

    @Test
    fun `checkpoints round-trip`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })
        session.observe(request())
        val store = InMemoryStreamCheckpointStore()

        session.save(store, "stream-1")
        val restored = StreamSession(decider(), clock = { manual() })
        assertTrue(restored.resume(store, "stream-1"))

        assertEquals(session.streamId, restored.streamId)
        assertEquals(1, restored.pending)
        assertEquals(1, restored.stats().observed)
    }

    @Test
    fun `an explicit stream id rejects a foreign checkpoint`() {
        val manual = clock()
        val source = StreamSession(decider(), streamId = "STR-A", clock = { manual() })
        source.observe(request())
        val store = InMemoryStreamCheckpointStore()
        source.save(store, "k")

        val target = StreamSession(decider(), streamId = "STR-B", clock = { manual() })

        assertFailsWith<IllegalArgumentException> { target.resume(store, "k") }
    }

    @Test
    fun `the attention budget is charged per decision`() {
        val manual = clock()
        val budget = HumanAttentionBudget(total = 1.0)
        val session = StreamSession(
            decide = { request ->
                listOf(
                    Decision(
                        verb = Verb.ASK,
                        confidence = 0.9,
                        reasonCode = "policy_rule",
                        rationale = "ask",
                        requiresApproval = true,
                    ),
                )
            },
            humanAttentionBudget = budget,
            clock = { manual() },
        )

        session.observe(request())

        assertEquals(0.5, budget.remaining(), 1e-9)
    }

    @Test
    fun `revise with stamps precomputed decisions`() {
        val manual = clock()
        val session = StreamSession(decider(), clock = { manual() })
        val first = session.observe(request()).single()
        val pushed = Decision(
            verb = Verb.ACT,
            confidence = 0.9,
            reasonCode = "policy_rule",
            rationale = "act",
            actionId = "a-1",
        )

        val revised = session.reviseWith(first, request(), listOf(pushed)).single()

        assertEquals(pushed.actionId, revised.actionId)
        assertEquals(first.decisionId, revised.supersedes)
        assertEquals(1, revised.revision)
    }

    @Test
    fun `the client streams decisions`() {
        val client = DecisionClient()
        val stream = client.stream(clock = { OffsetDateTime.parse(at) })

        val decisions = stream.observe(
            DecisionRequest(
                subject = "room-1",
                at = at,
                situation = Situation(id = "s-1", at = at, subject = "room-1"),
                options = listOf(ActionOption("a-1", Verb.WAIT, "wait")),
            ),
        )

        assertEquals(1, decisions.size)
        assertEquals("a-1", decisions.single().actionId)
    }

    @Test
    fun `constructor settings are validated`() {
        assertFailsWith<IllegalArgumentException> { StreamSession(decider(), capacity = 0) }
        assertFailsWith<IllegalArgumentException> { StreamSession(decider(), onFull = "keep") }
        assertFailsWith<IllegalArgumentException> { StreamSession(decider(), late = "keep") }
        assertFailsWith<IllegalArgumentException> { StreamSession(decider(), cooldownMs = -1) }
        assertFailsWith<IllegalArgumentException> {
            StreamSession(decider(), maxDecisionsPerWindow = 0)
        }
    }
}
