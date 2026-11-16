package dev.laix.decision.policies.action

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.iso
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class ActionPolicyTest {
    private fun situation(vararg attributes: Pair<String, Any?>): Situation =
        Situation(
            id = "SIT-1",
            at = iso(),
            subject = "demo",
            beliefs = listOf(Belief(id = "b-risk", proposition = "risk is real", confidence = 0.9)),
            attributes = attributes.toMap(),
        )

    private fun options(): List<ActionOption> =
        listOf(
            ActionOption("a-wait", Verb.WAIT, "observe", expectedBenefit = 0.2),
            ActionOption("a-ask", Verb.ASK, "request_evidence", expectedBenefit = 0.5),
            ActionOption("a-guide", Verb.GUIDE, "present_options", expectedBenefit = 0.6),
            ActionOption("a-act", Verb.ACT, "assign_team", expectedBenefit = 0.9),
            ActionOption("a-verify", Verb.VERIFY, "check_outcome", expectedBenefit = 0.5),
            ActionOption("a-escalate", Verb.ESCALATE, "escalate_commitment", expectedBenefit = 0.9),
        )

    private fun decide(
        situation: Situation,
        options: List<ActionOption> = options(),
        config: ActionPolicyConfig = ActionPolicyConfig(),
    ) = ActionPolicy(config).decide(
        ActionPolicyInput(situation = situation, options = options),
        decisionId = "D1",
        traceId = "T1",
    )

    @Test
    fun `acts when urgency and confidence are high`() {
        val decision = decide(situation("urgency" to 0.9))

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("a-act", decision.actionId)
        assertEquals(false, decision.requiresApproval)
        assertTrue(decision.rationale.contains("act thresholds"))
    }

    @Test
    fun `observes when more information is cheap`() {
        val observe = ActionOption("a-observe", Verb.OBSERVE, "take_another_look", expectedBenefit = 0.6)
        val decision = decide(situation("urgency" to 0.9, "needs_more_info" to true), options() + observe)

        assertEquals(Verb.OBSERVE, decision.verb)
        assertEquals("a-observe", decision.actionId)
    }

    @Test
    fun `asks when uncertain`() {
        val weak = Situation(
            id = "SIT-2",
            at = iso(),
            subject = "demo",
            beliefs = listOf(Belief(id = "b", proposition = "weak", confidence = 0.3)),
            attributes = mapOf("urgency" to 0.9),
        )

        assertEquals(Verb.ASK, decide(weak).verb)
    }

    @Test
    fun `escalates before acting on a breach`() {
        val decision = decide(situation("urgency" to 0.99, "deadline_breached" to true))

        assertEquals(Verb.ESCALATE, decision.verb)
    }

    @Test
    fun `verifies a pending outcome`() {
        val decision = decide(situation("urgency" to 0.99, "verification_due" to true))

        assertEquals(Verb.VERIFY, decision.verb)
    }

    @Test
    fun `guides a mid-urgency event`() {
        assertEquals(Verb.GUIDE, decide(situation("urgency" to 0.6)).verb)
    }

    @Test
    fun `waits when nothing clears the threshold`() {
        assertEquals(Verb.WAIT, decide(situation("urgency" to 0.1)).verb)
    }

    @Test
    fun `blocks actions that break hard constraints`() {
        val blocked = situation("urgency" to 0.99).copy(
            constraints = listOf(Constraint("c-lat", "latency", 100, hard = true)),
        )
        val slow = ActionOption("a-slow", Verb.ACT, "slow_act", latencyMs = 500, expectedBenefit = 0.99)
        val decision = decide(blocked, options() + slow)

        assertNotEquals("a-slow", decision.actionId)
        assertTrue(decision.constraintsApplied.any { it.contains("latency") })
        assertTrue(decision.alternatives.any { it["action_id"] == "a-slow" })
    }

    @Test
    fun `approval flag is scoped to actions`() {
        val guideSituation = Situation(
            id = "S",
            at = iso(),
            subject = "demo",
            beliefs = listOf(Belief(id = "b", proposition = "the condition is real", confidence = 0.9)),
            constraints = listOf(Constraint("approve", "approval", "required", hard = true)),
            attributes = mapOf("urgency" to 0.6),
        )
        val guide = decide(guideSituation)
        assertEquals(Verb.GUIDE, guide.verb)
        assertEquals(false, guide.requiresApproval)

        val act = decide(guideSituation.copy(id = "S2", attributes = mapOf("urgency" to 0.99)))
        assertEquals(Verb.ACT, act.verb)
        assertEquals(true, act.requiresApproval)
    }

    @Test
    fun `requires approval for destructive actions`() {
        val destructive = ActionOption(
            "a-delete",
            Verb.ACT,
            "delete",
            destructive = true,
            expectedBenefit = 0.99,
        )
        val decision = decide(situation("urgency" to 0.99), options() + destructive)

        assertEquals(Verb.ACT, decision.verb)
        assertEquals(true, decision.requiresApproval)
        assertTrue(decision.constraintsApplied.contains("approval:human-required"))
    }

    @Test
    fun `a hard safety constraint forces wait`() {
        val blocked = Situation(
            id = "S",
            at = iso(),
            subject = "demo",
            constraints = listOf(Constraint("safe", "safety", "blocked", hard = true)),
            attributes = mapOf("urgency" to 0.99),
        )
        val decision = decide(blocked)

        assertEquals(Verb.WAIT, decision.verb)
        assertTrue(decision.rationale.contains("safety"))
    }

    @Test
    fun `is deterministic`() {
        val policy = ActionPolicy()
        val input = ActionPolicyInput(situation("urgency" to 0.9), options())
        val first = policy.decide(input, "D", "T", "2026-01-01T00:00:00+00:00")
        val second = policy.decide(input, "D", "T", "2026-01-01T00:00:00+00:00")

        assertEquals(first.toMap(), second.toMap())
    }

    @Test
    fun `config is tunable`() {
        val strict = ActionPolicy(ActionPolicyConfig(actUrgency = 0.99, actConfidence = 0.99))

        assertEquals(
            Verb.GUIDE,
            strict.decide(ActionPolicyInput(situation("urgency" to 0.9), options())).verb,
        )
    }

    @Test
    fun `attributes carry the rounded inputs`() {
        val decision = decide(situation("urgency" to 0.91234, "uncertainty" to 0.123456))

        assertEquals(0.9123, decision.attributes["urgency"])
        assertEquals(0.1235, decision.attributes["uncertainty"])
        assertEquals("SIT-1", decision.situationId)
        assertEquals(ActionPolicy().version, decision.policyVersion)
        assertTrue(decision.createdAt != null)
    }
}
