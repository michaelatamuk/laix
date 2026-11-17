package dev.laix.decision.policies

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.policies.packs.PlanningPolicy
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import kotlin.test.Test
import kotlin.test.assertEquals

class RulesAndPlanningTest {
    private val at = "2026-11-01T10:00:00+00:00"

    @Test
    fun `rule policy takes the first match`() {
        val policy = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf("urgency" to mapOf("gte" to 0.8)),
                    verb = Verb.ACT,
                    reasonCode = "urgent",
                ),
                Rule(
                    condition = mapOf("kind" to "report"),
                    verb = Verb.GUIDE,
                    reasonCode = "report",
                ),
            ),
            name = "custom.rules",
        )

        val decision = policy.decide(
            DecisionRequest(
                subject = "s",
                at = at,
                attributes = mapOf("urgency" to 0.9, "kind" to "report"),
            ),
        ).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("urgent", decision.reasonCode)
        assertEquals("custom.rules", decision.policyVersion)
    }

    @Test
    fun `rule policy falls back`() {
        val policy = RulePolicy(
            listOf(Rule(mapOf("kind" to "report"), Verb.GUIDE, "report")),
        )

        val decision = policy.decide(DecisionRequest(subject = "s", at = at)).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("no_rule", decision.reasonCode)
    }

    @Test
    fun `rule conditions support in and contains`() {
        val policy = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf(
                        "tier" to mapOf("in" to listOf("gold", "silver")),
                        "tags" to mapOf("contains" to "urgent"),
                    ),
                    verb = Verb.ESCALATE,
                    reasonCode = "vip",
                ),
            ),
        )
        val decision = policy.decide(
            DecisionRequest(
                subject = "s",
                at = at,
                attributes = mapOf("tier" to "gold", "tags" to listOf("urgent", "billing")),
            ),
        ).single()

        assertEquals(Verb.ESCALATE, decision.verb)
    }

    @Test
    fun `planning acts on a due commitment`() {
        val ledger = CommitmentLedger(
            listOf(
                Commitment(id = "c1", subject = "send", due = "2026-11-01T09:00:00+00:00"),
            ),
        )
        val decision = PlanningPolicy(ledger).decide(
            DecisionRequest(subject = "s", at = at),
        ).single()

        assertEquals(Verb.ACT, decision.verb)
        assertEquals("due_commitment", decision.reasonCode)
        assertEquals("c1", decision.actionId)
    }

    @Test
    fun `planning waits when the commitment is not due`() {
        val ledger = CommitmentLedger(
            listOf(
                Commitment(id = "c1", subject = "send", due = "2026-11-01T12:00:00+00:00"),
            ),
        )
        val decision = PlanningPolicy(ledger).decide(
            DecisionRequest(subject = "s", at = at),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("not_due", decision.reasonCode)
    }

    @Test
    fun `planning asks when a commitment is blocked`() {
        val ledger = CommitmentLedger(
            listOf(
                Commitment(id = "c1", subject = "send", dependsOn = listOf("c0")),
            ),
        )
        val decision = PlanningPolicy(ledger).decide(
            DecisionRequest(subject = "s", at = at),
        ).single()

        assertEquals(Verb.ASK, decision.verb)
        assertEquals("blocked_commitment", decision.reasonCode)
        assertEquals("c1", decision.attributes["commitment_id"])
    }

    @Test
    fun `planning waits without commitments`() {
        val decision = PlanningPolicy(CommitmentLedger()).decide(
            DecisionRequest(subject = "s", at = at),
        ).single()

        assertEquals(Verb.WAIT, decision.verb)
        assertEquals("no_commitment", decision.reasonCode)
    }

    @Test
    fun `planning needs no options`() {
        val ledger = CommitmentLedger(
            listOf(Commitment(id = "c1", subject = "send", due = "2026-11-01T09:00:00+00:00")),
        )

        assertEquals(
            "due_commitment",
            PlanningPolicy(ledger).decide(
                DecisionRequest(subject = "s", at = at, options = listOf(ActionOption("a", Verb.ACT, "a"))),
            ).single().reasonCode,
        )
    }
}
