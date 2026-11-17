package dev.laix.decision.policies

import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.packs.ActivePerceptionPolicy
import dev.laix.decision.policies.packs.AllocationPolicy
import dev.laix.decision.policies.packs.EscalationPolicy
import dev.laix.decision.policies.packs.NegotiationPolicy
import dev.laix.decision.policies.packs.PreferenceElicitationPolicy
import dev.laix.decision.policies.packs.ReplanningPolicy
import dev.laix.decision.policies.packs.SafetyConstrainedPolicy
import dev.laix.decision.policies.packs.VerificationPolicy
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

class PolicyPacksTest {
    private fun request(vararg attributes: Pair<String, Any?>) = DecisionRequest(
        subject = "case-1",
        at = "2026-11-01T10:00:00+00:00",
        attributes = attributes.toMap(),
    )

    @Test
    fun `active perception observes when uncertainty is high`() {
        val decision = ActivePerceptionPolicy().decide(
            request(
                "uncertainty" to 0.8,
                "observations" to listOf(
                    mapOf("id" to "look-1", "information_gain" to 0.7, "cost" to 0.1),
                ),
            ),
        ).single()

        assertEquals(Verb.OBSERVE, decision.verb)
        assertEquals("observe", decision.intent?.capability)
    }

    @Test
    fun `active perception waits at low uncertainty`() {
        val decision = ActivePerceptionPolicy().decide(
            request("uncertainty" to 0.1, "observations" to emptyList<Any>()),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("uncertainty_low", decision.reasonCode)
    }

    @Test
    fun `safety acts only inside the risk limit`() {
        val decision = SafetyConstrainedPolicy().decide(
            request(
                "risk_limit" to 0.2,
                "options" to listOf(
                    mapOf("id" to "safe", "benefit" to 0.9, "risk" to 0.1),
                    mapOf("id" to "risky", "benefit" to 1.0, "risk" to 0.9),
                ),
            ),
        ).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("safe", decision.actionId)
    }

    @Test
    fun `safety waits when nothing is safe`() {
        val decision = SafetyConstrainedPolicy().decide(
            request(
                "risk_limit" to 0.1,
                "options" to listOf(mapOf("id" to "risky", "benefit" to 1.0, "risk" to 0.9)),
            ),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("no_safe_option", decision.reasonCode)
    }

    @Test
    fun `replanning picks a feasible plan`() {
        val decision = ReplanningPolicy().decide(
            request(
                "plans" to listOf(
                    mapOf("id" to "slow", "success_probability" to 0.95, "cost" to 10, "deadline_risk" to 0.1),
                    mapOf("id" to "fast", "success_probability" to 0.8, "cost" to 1, "deadline_risk" to 0.1),
                ),
                "min_success" to 0.7,
                "max_cost" to 5,
            ),
        ).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("fast", decision.actionId)
    }

    @Test
    fun `allocation funds requests inside the budget`() {
        val decision = AllocationPolicy().decide(
            request(
                "budget" to 10,
                "requests" to listOf(
                    mapOf("id" to "a", "value" to 6, "cost" to 4),
                    mapOf("id" to "b", "value" to 5, "cost" to 6),
                    mapOf("id" to "c", "value" to 9, "cost" to 20),
                ),
            ),
        ).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals(listOf("a", "b"), decision.intent?.args?.get("ids"))
    }

    @Test
    fun `negotiation counters accepts and escalates`() {
        val counter = NegotiationPolicy().decide(
            request("offer" to 5, "reservation" to 10, "target" to 20, "round" to 1),
        ).single()
        assertEquals(Verb.ACT, counter.verb)
        assertEquals("counter_offer", counter.intent?.capability)

        val accepted = NegotiationPolicy().decide(
            request("offer" to 12, "reservation" to 10, "target" to 20, "round" to 1),
        ).single()
        assertEquals(Verb.ACT, accepted.verb)
        assertEquals("accept_offer", accepted.intent?.capability)

        val escalated = NegotiationPolicy().decide(
            request("offer" to 5, "reservation" to 10, "target" to 20, "round" to 5),
        ).single()
        assertEquals(Verb.ESCALATE, escalated.verb)
    }

    @Test
    fun `preference elicitation asks the best question`() {
        val decision = PreferenceElicitationPolicy().decide(
            request(
                "uncertainty" to 0.8,
                "questions" to listOf(
                    mapOf("id" to "q1", "information_gain" to 0.2, "cost" to 1),
                    mapOf("id" to "q2", "information_gain" to 0.8, "cost" to 1),
                ),
            ),
        ).single()

        assertEquals(Verb.ASK, decision.verb)
        assertEquals("q2", decision.intent?.args?.get("id"))
    }

    @Test
    fun `verification picks the best check`() {
        val decision = VerificationPolicy().decide(
            request(
                "confidence" to 0.5,
                "required_confidence" to 0.8,
                "checks" to listOf(
                    mapOf("id" to "manual", "confidence_gain" to 0.2, "cost" to 1),
                    mapOf("id" to "api", "confidence_gain" to 0.8, "cost" to 1),
                ),
            ),
        ).single()

        assertEquals(Verb.VERIFY, decision.verb)
        assertEquals("api", decision.actionId)
        assertEquals("verify", decision.intent?.capability)
    }

    @Test
    fun `verification escalates without a path`() {
        val decision = VerificationPolicy().decide(
            request("confidence" to 0.3, "required_confidence" to 0.8, "checks" to emptyList<Any>()),
        ).single()

        assertEquals(Verb.ESCALATE, decision.verb)
        assertEquals("no_verification_path", decision.reasonCode)
        assertEquals("handover", decision.intent?.capability)
        assertEquals("human", decision.intent?.args?.get("target"))
    }

    @Test
    fun `verification is not needed when confident`() {
        val decision = VerificationPolicy().decide(
            request(
                "confidence" to 0.95,
                "required_confidence" to 0.8,
                "verification_due" to false,
                "checks" to emptyList<Any>(),
            ),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("verification_not_needed", decision.reasonCode)
    }

    @Test
    fun `escalation hands over to a target`() {
        val decision = EscalationPolicy().decide(
            request("severity" to 0.9, "severity_threshold" to 0.8, "target" to "manager"),
        ).single()

        assertEquals(Verb.ESCALATE, decision.verb)
        assertEquals("manager", decision.actionId)
        assertEquals("handover", decision.intent?.capability)
        assertEquals("manager", decision.intent?.args?.get("target"))
    }

    @Test
    fun `escalation waits within limits`() {
        val decision = EscalationPolicy().decide(
            request("severity" to 0.2, "severity_threshold" to 0.8, "confidence" to 0.9),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("within_limits", decision.reasonCode)
    }

    @Test
    fun `escalation asks for a target when missing`() {
        val decision = EscalationPolicy().decide(
            request("severity" to 0.9, "severity_threshold" to 0.8),
        ).single()

        assertEquals(Verb.ASK, decision.verb)
        assertEquals("target_required", decision.reasonCode)
    }

    @Test
    fun `policies carry their version and a non-empty intent when they act`() {
        val decision = SafetyConstrainedPolicy().decide(
            request(
                "options" to listOf(mapOf("id" to "safe", "benefit" to 0.9, "risk" to 0.1)),
            ),
        ).single()

        assertEquals("safety-constrained.v1", decision.policyVersion)
        assertNotNull(decision.intent as Intent?)
    }
}
