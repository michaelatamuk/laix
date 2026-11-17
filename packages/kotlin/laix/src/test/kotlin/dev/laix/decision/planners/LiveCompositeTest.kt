package dev.laix.decision.planners

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.planners.composite.LiveCompositePlanner
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LiveCompositeTest {
    private fun problem(
        options: List<ActionOption>,
        attributes: Map<String, Any?> = emptyMap(),
    ) = PlannerInput(
        subject = "choose",
        at = "2026-11-01T10:00:00+00:00",
        options = options,
        attributes = attributes,
    )

    @Test
    fun `combines all live concerns`() {
        val plan = LiveCompositePlanner().solve(
            problem(
                listOf(
                    ActionOption(
                        "fast",
                        Verb.ACT,
                        "fast",
                        expectedBenefit = 1.0,
                        reversible = false,
                        interruptCost = 0.6,
                        params = mapOf(
                            "commitments" to mapOf("violates" to listOf("c1")),
                        ),
                    ),
                    ActionOption(
                        "safe",
                        Verb.ACT,
                        "safe",
                        expectedBenefit = 0.6,
                        params = mapOf(
                            "commitments" to mapOf("fulfills" to listOf("c1")),
                        ),
                    ),
                ),
                mapOf(
                    "commitments" to CommitmentLedger(
                        listOf(
                            Commitment(
                                id = "c1",
                                subject = "send the report",
                                due = "2026-11-01T09:00:00+00:00",
                            ),
                        ),
                    ),
                ),
            ),
        )

        assertEquals("safe", plan.actionId)
        assertEquals("live_decision", plan.reasonCode)
        assertEquals(listOf("c1"), plan.attributes["commitments_fulfilled"])
        assertEquals(0.6, plan.attributes["utility"])
        assertTrue((plan.attributes["commitment_score"] as Double) > 0)
        assertEquals(0.0, plan.attributes["execution_score"] as Double, 0.0)
    }

    @Test
    fun `blocks a rejected approval`() {
        val plan = LiveCompositePlanner().solve(
            problem(
                listOf(
                    ActionOption("rejected", Verb.ACT, "rejected", expectedBenefit = 0.9),
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.6),
                ),
                mapOf("approvals" to mapOf("rejected" to "rejected")),
            ),
        )

        assertEquals("direct", plan.actionId)
    }

    @Test
    fun `respects the human attention budget`() {
        val plan = LiveCompositePlanner().solve(
            problem(
                listOf(
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.9),
                    ActionOption("act", Verb.ACT, "act", expectedBenefit = 0.6),
                ),
                mapOf("human_attention_budget" to HumanAttentionBudget(total = 1.0, spent = 0.9)),
            ),
        )

        assertEquals("act", plan.actionId)
    }

    @Test
    fun `no options waits`() {
        val plan = LiveCompositePlanner().solve(problem(emptyList()))

        assertEquals(Verb.WAIT, plan.verb)
        assertEquals("no_options", plan.reasonCode)
    }

    @Test
    fun `alternatives explain rejection`() {
        val plan = LiveCompositePlanner().solve(
            problem(
                listOf(
                    ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.7),
                    ActionOption(
                        "irreversible",
                        Verb.ACT,
                        "irreversible",
                        expectedBenefit = 0.7,
                        reversible = false,
                    ),
                ),
            ),
        )

        val rejected = plan.alternatives.first { it["action_id"] == "irreversible" }
        assertEquals("lower integrated score", rejected["rejected_because"])
    }
}
