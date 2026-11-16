package dev.laix.decision.contract

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.DecisionStatus
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.TargetMode
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityPlanner
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PlannerPolicyTest {
    private val request = DecisionRequest(
        subject = "choose",
        at = "2026-11-01T10:00:00Z",
        situation = Situation(
            id = "s-1",
            at = "2026-11-01T10:00:00Z",
            subject = "choose",
        ),
        options = listOf(
            ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
            ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.6),
        ),
        attributes = mapOf("tenant" to "acme", "utility" to "request"),
    )

    @Test
    fun `planner results become decisions`() {
        val decision = PlannerPolicy(UtilityPlanner()).decide(request).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("expected_utility", decision.reasonCode)
        assertEquals("bold", decision.actionId)
        assertEquals("planner.v1", decision.policyVersion)
        assertEquals(0.75, decision.score)
        assertEquals("acme", decision.attributes["tenant"])
    }

    @Test
    fun `planner attributes win over request attributes`() {
        val decision = PlannerPolicy(UtilityPlanner()).decide(request).single()

        assertEquals(0.75, decision.attributes["utility"])
        assertEquals("neutral", decision.attributes["risk_attitude"])
    }

    @Test
    fun `identifiers and trace ids are carried through`() {
        val decision = PlannerPolicy(UtilityPlanner())
            .decide(request, decisionId = "DEC-1", traceId = "TRC-1")
            .single()

        assertEquals("DEC-1", decision.decisionId)
        assertEquals("TRC-1", decision.traceId)
    }

    @Test
    fun `a custom policy name becomes the version`() {
        val policy = PlannerPolicy(UtilityPlanner(), name = "custom.v2")
        val decision = policy.decide(request).single()

        assertEquals("custom.v2", policy.version)
        assertEquals("custom.v2", decision.policyVersion)
    }

    @Test
    fun `basis starts with the reason and includes evidence and constraints`() {
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.9,
            reasonCode = "policy_rule",
            rationale = "because",
            evidence = listOf(
                dev.laix.decision.contracts.EvidenceRef(id = "e-1", kind = "document", quote = "quote"),
            ),
            intent = Intent("send", mapOf("to" to "ops")),
            constraintsApplied = listOf("safety:blocked", "safety:blocked"),
        )

        val basis = decision.basis()

        assertEquals(listOf("reason", "document", "intent", "constraint", "constraint"), basis.map { it["kind"] })
        assertEquals("policy_rule", basis.first()["ref"])
        assertEquals("send", basis[2]["ref"])
    }

    @Test
    fun `decisions round-trip through maps`() {
        val original = Decision(
            verb = Verb.VERIFY,
            confidence = 1.4,
            reasonCode = "policy_rule",
            rationale = "verify it",
            actionId = "a-1",
            status = DecisionStatus.PROVISIONAL,
            target = TargetMode.SOME,
            recipients = listOf("ops"),
            revision = 2,
        )
        val restored = Decision.fromMap(original.toMap())

        assertEquals(Verb.VERIFY, restored.verb)
        assertEquals(1.0, restored.confidence)
        assertEquals(original.copy(confidence = 1.0), restored)
        assertTrue(restored.basis().isNotEmpty())
    }
}
