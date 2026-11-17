package dev.laix.decision.planners

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.planners.sequence.CABBPlanner
import dev.laix.decision.planners.sequence.DecisionScenario
import dev.laix.decision.planners.sequence.DecisionStep
import dev.laix.decision.planners.sequence.ReplanPlanner
import dev.laix.decision.planners.sequence.RolloutPlanner
import dev.laix.decision.planners.sequence.planDecisions
import dev.laix.decision.planners.sequence.replanDecisions
import dev.laix.decision.planners.sequence.rolloutDecisions
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class CabbTest {
    private fun scenario() = DecisionScenario(
        steps = listOf(
            DecisionStep(
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption(
                        "pay",
                        Verb.ACT,
                        "pay",
                        expectedBenefit = 0.95,
                        risk = 0.05,
                        requiresApproval = true,
                        reversible = false,
                        interruptCost = 0.6,
                        params = mapOf("commitments" to mapOf("violates" to listOf("c1"))),
                    ),
                    ActionOption(
                        "ask",
                        Verb.ASK,
                        "ask",
                        expectedBenefit = 0.6,
                        interruptCost = 0.2,
                        params = mapOf("commitments" to mapOf("fulfills" to listOf("c1"))),
                    ),
                ),
            ),
            DecisionStep(
                at = "2026-11-01T11:00:00+00:00",
                options = listOf(
                    ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.2),
                    ActionOption("verify", Verb.VERIFY, "verify", expectedBenefit = 0.4),
                ),
            ),
        ),
        commitments = listOf(
            Commitment(
                id = "c1",
                subject = "ask before paying",
                due = "2026-11-01T09:00:00+00:00",
            ),
        ),
        humanAttentionBudget = HumanAttentionBudget(total = 2.0, spent = 0.5),
    )

    private fun greedyTrap() = DecisionScenario(
        steps = listOf(
            DecisionStep(
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(ActionOption("start", Verb.WAIT, "start", expectedBenefit = 0.0)),
            ),
            DecisionStep(
                at = "2026-11-01T10:10:00+00:00",
                options = listOf(
                    ActionOption("big", Verb.ACT, "big", expectedBenefit = 1.0, interruptCost = 0.9),
                    ActionOption("small", Verb.ACT, "small", expectedBenefit = 0.6, interruptCost = 0.3),
                ),
            ),
            DecisionStep(
                at = "2026-11-01T10:20:00+00:00",
                options = listOf(
                    ActionOption("bonus", Verb.ACT, "bonus", expectedBenefit = 1.0, interruptCost = 0.6),
                    ActionOption("nothing", Verb.WAIT, "nothing", expectedBenefit = 0.1),
                ),
            ),
        ),
        humanAttentionBudget = HumanAttentionBudget(total = 1.0, spent = 0.0),
    )

    @Test
    fun `cabb keeps the commitment first`() {
        val plan = CABBPlanner().plan(scenario())

        assertEquals("ask", plan.actions.first())
        assertEquals(2, plan.actions.size)
        assertEquals(emptyList(), plan.violations)
        assertTrue(plan.attentionSpent <= 1.5)
        assertTrue(plan.nodes > 0)
        assertEquals(true, plan.optimal)
    }

    @Test
    fun `evaluate replays the optimal plan`() {
        val planner = CABBPlanner()
        val plan = planner.plan(scenario())
        val replay = planner.evaluate(scenario(), plan.actions)

        assertEquals(plan.score, replay.score)
        assertEquals(plan.actions, replay.actions)
    }

    @Test
    fun `cabb empty scenario`() {
        val plan = planDecisions(DecisionScenario(emptyList()))

        assertEquals(emptyList(), plan.actions)
        assertEquals(0.0, plan.score)
        assertEquals(true, plan.optimal)
    }

    @Test
    fun `rollout matches the commitment first choice`() {
        val plan = RolloutPlanner().plan(scenario())

        assertEquals("ask", plan.actions.first())
        assertEquals(2, plan.actions.size)
        assertEquals(false, plan.optimal)
    }

    @Test
    fun `rollout empty scenario`() {
        val plan = rolloutDecisions(DecisionScenario(emptyList()))

        assertEquals(emptyList(), plan.actions)
        assertEquals(0.0, plan.score)
    }

    @Test
    fun `replan after the first step`() {
        val result = ReplanPlanner().replan(scenario(), listOf("ask"))

        assertEquals(listOf("ask"), result.executed)
        assertEquals(listOf("verify"), result.actions)
        assertEquals(true, result.optimal)
        assertTrue(result.reason.startsWith("replanned"))
    }

    @Test
    fun `replan with nothing left`() {
        val result = replanDecisions(scenario(), listOf("ask", "verify"))

        assertEquals(emptyList(), result.actions)
        assertEquals("nothing left to replan", result.reason)
    }

    @Test
    fun `cabb beats greedy rollout on an attention tradeoff`() {
        val exact = CABBPlanner().plan(greedyTrap())
        val greedy = RolloutPlanner().plan(greedyTrap())

        assertEquals(listOf("start", "small", "bonus"), exact.actions)
        assertEquals(listOf("start", "big", "nothing"), greedy.actions)
        assertTrue(exact.score > greedy.score)
    }
}
