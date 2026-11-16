package dev.laix.decision

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.signals.Signal
import dev.laix.decision.signals.SignalContext
import java.time.OffsetDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class DecideTest {
    private val at = "2026-11-02T10:00:00+02:00"

    private fun actionRequest(): DecisionRequest =
        DecisionRequest(
            subject = "room-1",
            at = at,
            situation = Situation(id = "s-1", at = at, subject = "room-1"),
            options = listOf(ActionOption(id = "a-1", verb = Verb.WAIT, name = "wait")),
        )

    @Test
    fun `action decisions carry ids`() {
        val decision = decide(actionRequest()).single()

        assertTrue(decision.decisionId.startsWith("DEC-"))
        assertTrue(decision.traceId.startsWith("TRC-"))
    }

    @Test
    fun `a host can supply the id factory`() {
        val decision = decide(actionRequest(), idFactory = { prefix -> "$prefix-fixed" }).single()

        assertEquals("DEC-fixed", decision.decisionId)
        assertEquals("TRC-fixed", decision.traceId)
    }

    @Test
    fun `a policy decision without ids gets them`() {
        val policy = object : DecisionPolicy {
            override val name: String = "always-wait"

            override fun decide(request: DecisionRequest): List<Decision> =
                listOf(
                    Decision(
                        verb = Verb.WAIT,
                        confidence = 0.5,
                        reasonCode = "policy_rule",
                        rationale = "this policy always waits",
                    ),
                )
        }

        val decision = decide(actionRequest(), policy = policy).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertTrue(decision.decisionId.startsWith("DEC-"))
        assertTrue(decision.traceId.startsWith("TRC-"))
    }

    @Test
    fun `attention decisions keep their trace id and get a decision id`() {
        val request = DecisionRequest(
            subject = "room-1",
            at = at,
            signals = listOf(Signal(id = "s-1", kind = "power", severity = "high", confidence = 0.9)),
            context = SignalContext(
                now = OffsetDateTime.parse(at),
                quietHours = null,
            ),
        )

        val decision = decide(request).single()

        assertTrue(decision.traceId.startsWith("tr-"))
        assertTrue(decision.decisionId.startsWith("DEC-"))
        assertEquals(Verb.GUIDE, decision.verb)
        assertEquals("worth_surfacing", decision.reasonCode)
        assertEquals("worth_surfacing", decision.rationale)
    }

    @Test
    fun `confidence provenance is carried onto the decision`() {
        val request = actionRequest().copy(
            confidence = 0.8,
            confidenceSource = "model",
            calibrated = true,
        )
        val decision = decide(request).single()

        assertEquals("model", decision.confidenceSource)
        assertEquals(true, decision.calibrated)
        assertEquals(0.8, decision.confidence)
    }

    @Test
    fun `a request without a route is rejected`() {
        val request = DecisionRequest(subject = "room-1", at = at)

        assertFailsWith<IllegalArgumentException> { decide(request) }
    }

    @Test
    fun `attention needs a signal context`() {
        val request = DecisionRequest(
            subject = "room-1",
            at = at,
            signals = listOf(Signal(id = "s-1", kind = "power")),
            context = "now",
        )

        assertFailsWith<IllegalArgumentException> { decide(request) }
    }

    @Test
    fun `maps are coerced into decisions`() {
        val decision = coerce(
            mapOf(
                "verb" to "verify",
                "confidence" to 1.5,
                "reason_code" to "policy_rule",
                "deliver" to false,
                "revision" to 3,
                "status" to "provisional",
                "target" to "some",
                "recipients" to listOf("ops"),
            ),
        )

        assertEquals(Verb.VERIFY, decision.verb)
        assertEquals(1.0, decision.confidence)
        assertEquals(false, decision.deliver)
        assertEquals(3, decision.revision)
        assertEquals(listOf("ops"), decision.recipients)
    }
}
