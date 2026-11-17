package dev.laix.decision.planners

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.explain.counterfactualAttribution
import dev.laix.decision.planners.history.ContinuityRecord
import dev.laix.decision.planners.history.repairContinuity
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class RepairAndCounterfactualTest {
    @Test
    fun `repair supersedes the cheaper conflicting record`() {
        val plan = repairContinuity(
            listOf(
                ContinuityRecord(
                    id = "approval-1",
                    kind = "approval",
                    status = "rejected",
                    refs = listOf("order-1"),
                    cost = 1.0,
                ),
                ContinuityRecord(
                    id = "receipt-1",
                    kind = "receipt",
                    status = "executed",
                    refs = listOf("order-1"),
                    cost = 3.0,
                ),
            ),
        )

        assertEquals(listOf("approval-1" to "receipt-1"), plan.conflicts)
        assertEquals("approval-1", plan.actions.first().recordId)
        assertEquals("superseded", plan.actions.first().toStatus)
        assertEquals(1.0, plan.totalCost)
        assertEquals(false, plan.consistent)
    }

    @Test
    fun `repair is empty for a consistent history`() {
        val plan = repairContinuity(
            listOf(ContinuityRecord(id = "decision-1", kind = "decision", status = "final")),
        )

        assertEquals(emptyList(), plan.conflicts)
        assertEquals(emptyList(), plan.actions)
        assertEquals(0.0, plan.totalCost)
        assertEquals(true, plan.consistent)
    }

    @Test
    fun `exact repair beats greedy on a star`() {
        val records = listOf(
            ContinuityRecord("a", "decision", "final", conflicts = listOf("b"), cost = 1.0),
            ContinuityRecord("b", "decision", "final", conflicts = listOf("c", "d"), cost = 2.0),
            ContinuityRecord("c", "decision", "final", cost = 1.0),
            ContinuityRecord("d", "decision", "final", cost = 1.0),
        )

        val greedy = repairContinuity(records)
        val exact = repairContinuity(records, exact = true)

        assertEquals(3.0, greedy.totalCost)
        assertEquals(2.0, exact.totalCost)
        assertEquals(listOf("b"), exact.actions.map { it.recordId })
        assertEquals("exact", exact.method)
    }

    @Test
    fun `explicit conflicts are honoured`() {
        val plan = repairContinuity(
            listOf(
                ContinuityRecord(
                    id = "a",
                    kind = "decision",
                    status = "final",
                    conflicts = listOf("b"),
                    cost = 0.1,
                ),
                ContinuityRecord(id = "b", kind = "decision", status = "final", cost = 0.2),
            ),
        )

        assertEquals("a", plan.actions.first().recordId)
    }

    private fun decision() = Decision(
        verb = Verb.ASK,
        confidence = 0.8,
        reasonCode = "value_of_decision",
        rationale = "ask balances the terms",
        actionId = "ask",
        score = 1.0,
        attributes = linkedMapOf(
            "utility" to 0.5,
            "commitment_score" to 0.6,
            "execution_score" to 0.0,
            "human_attention_score" to -0.1,
        ),
        alternatives = listOf(
            linkedMapOf(
                "action_id" to "pay",
                "verb" to "act",
                "utility" to 0.8,
                "commitment" to -0.2,
                "execution" to -0.3,
                "human_attention" to -0.1,
                "total" to 0.2,
            ),
            linkedMapOf(
                "action_id" to "wait",
                "verb" to "wait",
                "utility" to 0.2,
                "commitment" to 0.0,
                "execution" to 0.0,
                "human_attention" to 0.0,
                "total" to 0.2,
            ),
        ),
    )

    @Test
    fun `counterfactual finds the smallest gap`() {
        val report = counterfactualAttribution(decision())

        assertEquals("ask", report.chosenId)
        assertNotNull(report.minimal)
        assertEquals("pay", report.minimal?.alternativeId)
        assertTrue(report.minimal!!.delta in 0.8..0.80001)
        assertEquals(
            report.counterfactuals.sortedBy { it.delta },
            report.counterfactuals,
        )
    }

    @Test
    fun `counterfactual handles a missing component`() {
        val report = counterfactualAttribution(
            Decision(
                verb = Verb.ASK,
                confidence = 0.8,
                reasonCode = "x",
                rationale = "x",
                actionId = "ask",
                score = 1.0,
                alternatives = listOf(mapOf("action_id" to "pay", "total" to 0.2)),
            ),
        )

        assertEquals(emptyList(), report.counterfactuals)
        assertNull(report.minimal)
    }
}
