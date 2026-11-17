package dev.laix.decision.outcomes

import dev.laix.decision.contracts.Verb
import dev.laix.decision.outcomes.attention.SignalAttentionLog
import dev.laix.decision.outcomes.attention.SignalAttentionOutcome
import dev.laix.decision.outcomes.attention.labelForFeedback
import dev.laix.decision.outcomes.attention.resultForReason
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SignalAttentionOutcomesTest {
    private fun outcome(
        signalId: String,
        kind: String,
        result: OutcomeLabel,
        reason: String? = null,
        score: Double? = null,
    ) = SignalAttentionOutcome(
        signalId = signalId,
        kind = kind,
        verb = Verb.GUIDE,
        result = result,
        reasonCode = reason,
        score = score,
    )

    @Test
    fun `reasons and feedback map to labels`() {
        assertEquals(OutcomeLabel.HURT, resultForReason("false_alarm"))
        assertEquals(OutcomeLabel.HURT, resultForReason("data_error"))
        assertEquals(OutcomeLabel.NEUTRAL, resultForReason("design_change"))
        assertEquals(OutcomeLabel.NEUTRAL, resultForReason("no_action"))
        assertEquals(OutcomeLabel.UNKNOWN, resultForReason(null))
        assertEquals(OutcomeLabel.HELPED, labelForFeedback("accepted"))
        assertEquals(OutcomeLabel.HURT, labelForFeedback("dismissed", "false_alarm"))
    }

    @Test
    fun `the log reports precision and hazard`() {
        val log = SignalAttentionLog()
        assertNull(log.precision())

        log.record(outcome("a", "kind-a", OutcomeLabel.HELPED, score = 80.0))
        log.record(outcome("b", "kind-a", OutcomeLabel.HURT, reason = "false_alarm", score = 70.0))
        log.record(outcome("c", "kind-b", OutcomeLabel.NEUTRAL, reason = "design_change", score = 40.0))

        assertEquals(1.0 / 3.0, log.precision()!!, 1e-9)
        assertEquals(1.0 / 3.0, log.hazardRate()!!, 1e-9)
        assertEquals(0.5, log.precision("kind-a")!!, 1e-9)
        assertEquals(0.0, log.adjustment("kind-a"))
        assertEquals(3, log.total())
    }

    @Test
    fun `calibration has one row per bucket`() {
        val log = SignalAttentionLog()
        log.record(outcome("a", "k", OutcomeLabel.HELPED, score = 10.0))
        log.record(outcome("b", "k", OutcomeLabel.HURT, score = 90.0))

        val rows = log.calibration()

        assertEquals(4, rows.size)
        assertEquals(1, rows[0]["n"])
        assertEquals(1.0, rows[0]["rate"])
        assertEquals(1, rows[3]["n"])
        assertEquals(0.0, rows[3]["rate"])
    }

    @Test
    fun `by kind exposes counts and adjustments`() {
        val log = SignalAttentionLog()
        log.record(outcome("a", "kind-a", OutcomeLabel.HELPED))
        log.record(outcome("b", "kind-a", OutcomeLabel.HURT))

        val byKind = log.byKind()

        assertEquals(setOf("kind-a"), byKind.keys)
        assertEquals(1, byKind.getValue("kind-a")["helped"])
        assertEquals(1, byKind.getValue("kind-a")["hurt"])
        assertEquals(0.5, byKind.getValue("kind-a")["precision"])
    }

    @Test
    fun `the log is bounded`() {
        val log = SignalAttentionLog(limit = 2)
        log.record(outcome("a", "k", OutcomeLabel.HELPED))
        log.record(outcome("b", "k", OutcomeLabel.HELPED))
        log.record(outcome("c", "k", OutcomeLabel.HELPED))

        assertEquals(2, log.records.size)
        assertEquals(listOf("b", "c"), log.records.map { it.signalId })
    }

    @Test
    fun `outcomes serialise`() {
        val payload = outcome("a", "k", OutcomeLabel.HELPED, score = 80.0).asMap()

        assertEquals("a", payload["signal_id"])
        assertEquals("guide", payload["verb"])
        assertEquals("helped", payload["result"])
        assertTrue(payload.containsKey("score"))
    }
}
