package dev.laix.decision.planners

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.planners.attention.HumanAttentionEffect
import dev.laix.decision.planners.attention.HumanAttentionPlanner
import dev.laix.decision.planners.attention.HumanAttentionWeights
import dev.laix.decision.planners.execution.ExecutionEffect
import dev.laix.decision.planners.execution.ExecutionRiskPlanner
import dev.laix.decision.planners.execution.ExecutionWeights
import dev.laix.decision.planners.utility.UtilityPlanner
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

class PlannersBatchThreeTest {
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
    fun `execution prefers a reversible option`() {
        val plan = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("reversible", Verb.ACT, "reversible", expectedBenefit = 0.7),
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

        assertEquals("reversible", plan.actionId)
        assertEquals("execution_aware", plan.reasonCode)
    }

    @Test
    fun `execution penalizes unknown outcomes and recovery`() {
        val unknown = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("known", Verb.ACT, "known", expectedBenefit = 0.7),
                    ActionOption(
                        "unknown",
                        Verb.ACT,
                        "unknown",
                        expectedBenefit = 0.8,
                        params = mapOf("unknown_risk" to 0.8),
                    ),
                ),
            ),
        )
        assertEquals("known", unknown.actionId)

        val recovery = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("cheap", Verb.ACT, "cheap", expectedBenefit = 0.7),
                    ActionOption(
                        "expensive",
                        Verb.ACT,
                        "expensive",
                        expectedBenefit = 0.8,
                        params = mapOf("execution" to mapOf("recovery_cost" to 1.0)),
                    ),
                ),
            ),
        )
        assertEquals("cheap", recovery.actionId)
    }

    @Test
    fun `execution penalizes an approval step`() {
        val plan = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "approval",
                        Verb.ACT,
                        "approval",
                        expectedBenefit = 0.75,
                        requiresApproval = true,
                    ),
                ),
            ),
        )

        assertEquals("direct", plan.actionId)
    }

    @Test
    fun `execution matches utility without execution facts`() {
        val options = listOf(
            ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
            ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.6),
        )
        val problem = problem(options)

        assertEquals(
            UtilityPlanner().solve(problem).actionId,
            ExecutionRiskPlanner().solve(problem).actionId,
        )
    }

    @Test
    fun `execution reads receipt state`() {
        val unknown = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("known", Verb.ACT, "known", expectedBenefit = 0.7),
                    ActionOption("unknown", Verb.ACT, "unknown", expectedBenefit = 0.8),
                ),
                mapOf(
                    "execution_receipts" to listOf(
                        mapOf("action_name" to "unknown", "status" to "unknown"),
                    ),
                ),
            ),
        )
        assertEquals("known", unknown.actionId)

        val failed = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("known", Verb.ACT, "known", expectedBenefit = 0.7),
                    ActionOption("failed", Verb.ACT, "failed", expectedBenefit = 0.8),
                ),
                mapOf("execution_state" to mapOf("failed" to "failed")),
            ),
        )
        assertEquals("known", failed.actionId)

        val pending = ExecutionRiskPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption("pending", Verb.ACT, "pending", expectedBenefit = 0.75),
                ),
                mapOf("execution_state" to mapOf("pending" to "pending")),
            ),
        )
        assertEquals("direct", pending.actionId)
    }

    @Test
    fun `execution clamps effects and rejects weights`() {
        assertEquals(1.0, ExecutionEffect(unknownRisk = 2.0).unknownRisk)
        assertEquals(0.0, ExecutionEffect(unknownRisk = -1.0).unknownRisk)
        assertFailsWith<IllegalArgumentException> { ExecutionWeights(recovery = -1.0) }
    }

    @Test
    fun `human attention prefers the low-attention option`() {
        val plan = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "guide",
                        Verb.GUIDE,
                        "guide",
                        expectedBenefit = 0.75,
                        interruptCost = 0.8,
                    ),
                ),
            ),
        )

        assertEquals("direct", plan.actionId)
        assertEquals("human_attention_aware", plan.reasonCode)
    }

    @Test
    fun `human attention blocks options without budget`() {
        val plan = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.9),
                    ActionOption("act", Verb.ACT, "act", expectedBenefit = 0.6),
                ),
                mapOf(
                    "human_attention_budget" to 0.2,
                    "human_attention_spent" to 0.2,
                ),
            ),
        )

        assertEquals("act", plan.actionId)
        assertNull(plan.attributes["human_attention_budget_blocked"])
    }

    @Test
    fun `human attention waits when everything needs attention`() {
        val plan = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.9),
                    ActionOption("guide", Verb.GUIDE, "guide", expectedBenefit = 0.8),
                ),
                mapOf("human_attention_budget" to 0.0),
            ),
        )

        assertEquals(Verb.WAIT, plan.verb)
        assertEquals("human_attention_budget_exhausted", plan.reasonCode)
    }

    @Test
    fun `human attention charges approval and respects approval state`() {
        val costs = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "approval",
                        Verb.ACT,
                        "approval",
                        expectedBenefit = 0.75,
                        requiresApproval = true,
                    ),
                ),
            ),
        )
        assertEquals("direct", costs.actionId)

        val approved = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "approved",
                        Verb.ACT,
                        "approved",
                        expectedBenefit = 0.75,
                        requiresApproval = true,
                    ),
                ),
                mapOf("approvals" to mapOf("approved" to "approved")),
            ),
        )
        assertEquals("approved", approved.actionId)

        val rejected = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("rejected", Verb.ACT, "rejected", expectedBenefit = 0.9),
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.6),
                ),
                mapOf("approvals" to mapOf("rejected" to "rejected")),
            ),
        )
        assertEquals("direct", rejected.actionId)

        val pending = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption(
                        "pending",
                        Verb.ACT,
                        "pending",
                        expectedBenefit = 0.75,
                        requiresApproval = true,
                    ),
                ),
                mapOf("approvals" to mapOf("pending" to "pending")),
            ),
        )
        assertEquals("direct", pending.actionId)
    }

    @Test
    fun `human attention shares a budget object`() {
        val budget = HumanAttentionBudget(total = 1.0, spent = 0.9)
        val plan = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.9),
                    ActionOption("act", Verb.ACT, "act", expectedBenefit = 0.6),
                ),
                mapOf("human_attention_budget" to budget),
            ),
        )

        assertEquals("act", plan.actionId)
        assertEquals(0.1, budget.remaining(), 1e-9)
        assertEquals(0.0, budget.spend(0.1), 1e-9)
    }

    @Test
    fun `human attention matches utility without attention facts`() {
        val options = listOf(
            ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
            ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.6),
        )
        val problem = problem(options)

        assertEquals(
            UtilityPlanner().solve(problem).actionId,
            HumanAttentionPlanner().solve(problem).actionId,
        )
    }

    @Test
    fun `human attention clamps effects and rejects weights`() {
        assertEquals(1.0, HumanAttentionEffect(interruptCost = 2.0).interruptCost)
        assertEquals(0.0, HumanAttentionEffect(interruptCost = -1.0).interruptCost)
        assertFailsWith<IllegalArgumentException> { HumanAttentionWeights(interrupt = -1.0) }
        assertFailsWith<IllegalArgumentException> { HumanAttentionBudget(total = -1.0) }
    }

    @Test
    fun `human attention reports alternatives`() {
        val plan = HumanAttentionPlanner().solve(
            problem(
                listOf(
                    ActionOption("direct", Verb.ACT, "direct", expectedBenefit = 0.7),
                    ActionOption("guide", Verb.GUIDE, "guide", expectedBenefit = 0.75, interruptCost = 0.8),
                ),
                mapOf("human_attention_budget" to 0.0),
            ),
        )

        assertTrue(plan.alternatives.isNotEmpty())
        assertTrue(plan.alternatives.all { it.containsKey("rejected_because") })
    }
}
