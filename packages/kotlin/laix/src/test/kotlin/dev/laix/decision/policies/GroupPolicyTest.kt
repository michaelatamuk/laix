package dev.laix.decision.policies

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.TargetMode
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.packs.GroupPolicy
import dev.laix.decision.policies.packs.TargetedPolicy
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class GroupPolicyTest {
    private val request = DecisionRequest(subject = "a task", at = "2026-11-01T10:00:00+00:00")

    private fun fakePolicy(): DecisionPolicy = DecisionPolicy {
        listOf(
            Decision(
                verb = Verb.GUIDE,
                confidence = 0.9,
                reasonCode = "share",
                rationale = "share",
                attributes = mapOf("topic" to "math", "health" to "private"),
            ),
        )
    }

    private fun richPolicy(): DecisionPolicy = DecisionPolicy {
        listOf(
            Decision(
                verb = Verb.GUIDE,
                confidence = 0.9,
                reasonCode = "share",
                rationale = "the health record is private",
                evidence = listOf(
                    EvidenceRef(id = "e1", kind = "note", source = "health"),
                    EvidenceRef(id = "e2", kind = "note", source = "catalog"),
                ),
                intent = Intent("share", mapOf("health" to "private", "topic" to "math")),
                undoHint = "health record",
                alternatives = listOf(mapOf("health" to "private", "ok" to 1)),
                attributes = mapOf(
                    "topic" to "math",
                    "nested" to mapOf("health" to "private", "visible" to 1),
                    "items" to listOf(mapOf("health" to "private", "ok" to 2)),
                ),
            ),
        )
    }

    @Test
    fun `group policy sets the target and masks private state`() {
        val policy = GroupPolicy(
            fakePolicy(),
            target = "all",
            recipients = listOf("alice", "ben", "chris"),
            privateAttributes = listOf("health"),
        )
        val decision = policy.decide(request).single()

        assertEquals(TargetMode.ALL, decision.target)
        assertEquals(listOf("alice", "ben", "chris"), decision.recipients)
        assertEquals(mapOf("topic" to "math"), decision.attributes)
    }

    @Test
    fun `group policy masks nested attributes, evidence and rationale`() {
        val policy = GroupPolicy(
            richPolicy(),
            privateAttributes = listOf("health"),
            privateEvidence = listOf("health"),
            rationale = "shared summary",
            undoHint = "shared undo",
        )
        val decision = policy.decide(request).single()

        assertEquals("shared summary", decision.rationale)
        assertEquals("shared undo", decision.undoHint)
        assertEquals(listOf("e2"), decision.evidence.map { it.id })
        assertEquals(mapOf("topic" to "math"), decision.intent?.args)
        assertEquals(listOf(mapOf("ok" to 1)), decision.alternatives)
        assertEquals(
            mapOf(
                "topic" to "math",
                "nested" to mapOf("visible" to 1),
                "items" to listOf(mapOf("ok" to 2)),
            ),
            decision.attributes,
        )
    }

    @Test
    fun `targeted policy applies request targets`() {
        val policy = TargetedPolicy(fakePolicy())
        val decision = policy.decide(
            request.copy(target = TargetMode.SOME, recipients = listOf("ops")),
        ).single()

        assertEquals(TargetMode.SOME, decision.target)
        assertEquals(listOf("ops"), decision.recipients)
    }

    @Test
    fun `targeted policy can force a target`() {
        val policy = TargetedPolicy(fakePolicy(), target = "peer", recipients = listOf("lead"))
        val decision = policy.decide(request).single()

        assertEquals(TargetMode.PEER, decision.target)
        assertEquals(listOf("lead"), decision.recipients)
    }

    @Test
    fun `unknown targets are rejected`() {
        assertFailsWith<IllegalArgumentException> { TargetedPolicy(fakePolicy(), target = "nobody") }
        assertFailsWith<IllegalArgumentException> { GroupPolicy(fakePolicy(), target = "nobody") }
    }
}
