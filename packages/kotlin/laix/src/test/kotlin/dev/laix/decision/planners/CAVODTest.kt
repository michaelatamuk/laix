package dev.laix.decision.planners

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.planners.decisionvalue.CAVODPlanner
import dev.laix.decision.planners.decisionvalue.CAVODWeights
import dev.laix.decision.planners.pomdp.ObservationProbability
import dev.laix.decision.planners.pomdp.PomdpModel
import dev.laix.decision.planners.pomdp.PomdpTransition
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class CAVODTest {
    private fun problem() = PlannerInput(
        subject = "invoice 4832",
        at = "2026-11-01T10:00:00+00:00",
        options = listOf(
            ActionOption(
                "pay",
                Verb.ACT,
                "pay the invoice",
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
                "ask the owner",
                expectedBenefit = 0.6,
                interruptCost = 0.2,
                params = mapOf("commitments" to mapOf("fulfills" to listOf("c1"))),
            ),
            ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.2),
        ),
        attributes = mapOf(
            "commitments" to CommitmentLedger(
                listOf(
                    Commitment(
                        id = "c1",
                        subject = "ask the owner before paying",
                        due = "2026-11-01T09:00:00+00:00",
                    ),
                ),
            ),
            "human_attention_budget" to HumanAttentionBudget(total = 2.0, spent = 0.5),
            "uncertainty" to 0.8,
        ),
    )

    @Test
    fun `adds information value and chooses ask`() {
        val plan = CAVODPlanner().solve(problem())

        assertEquals(Verb.ASK, plan.verb)
        assertEquals("ask", plan.actionId)
        assertEquals("value_of_decision", plan.reasonCode)
        assertEquals("ca_vod.v1", plan.attributes["algorithm"])
        assertTrue((plan.attributes["information_value"] as Double) > 0)
        assertEquals(0.8, plan.attributes["uncertainty"])
        assertTrue(plan.alternatives.isNotEmpty())
    }

    @Test
    fun `waits when there are no options`() {
        val plan = CAVODPlanner().solve(
            PlannerInput(
                subject = "empty",
                at = "2026-11-01T10:00:00+00:00",
                options = emptyList(),
            ),
        )

        assertEquals(Verb.WAIT, plan.verb)
        assertEquals("no_options", plan.reasonCode)
    }

    @Test
    fun `uses belief state future value`() {
        val model = PomdpModel(
            states = listOf("safe", "risky"),
            actions = listOf("act", "ask", "wait"),
            observations = listOf("ok", "good", "bad"),
            transitions = listOf(
                PomdpTransition("safe", "act", "safe", reward = 1.0),
                PomdpTransition("risky", "act", "risky", reward = -1.0),
                PomdpTransition("safe", "ask", "safe"),
                PomdpTransition("risky", "ask", "risky"),
                PomdpTransition("safe", "wait", "safe"),
                PomdpTransition("risky", "wait", "risky"),
            ),
            observationTable = listOf(
                ObservationProbability("safe", "act", "ok"),
                ObservationProbability("risky", "act", "ok"),
                ObservationProbability("safe", "ask", "good"),
                ObservationProbability("risky", "ask", "bad"),
                ObservationProbability("safe", "wait", "ok"),
                ObservationProbability("risky", "wait", "ok"),
            ),
            discount = 0.9,
            horizon = 2,
        )
        val plan = CAVODPlanner(
            pomdpModel = model,
            belief = mapOf("safe" to 0.5, "risky" to 0.5),
        ).solve(
            PlannerInput(
                subject = "belief",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("act", Verb.ACT, "act", expectedBenefit = 0.55),
                    ActionOption("ask", Verb.ASK, "ask", expectedBenefit = 0.2),
                    ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.1),
                ),
            ),
        )

        assertEquals("ask", plan.actionId)
        assertTrue((plan.attributes["future_value"] as Double) > 0)
        assertEquals(2, plan.attributes["horizon"])
    }

    @Test
    fun `weights reject negatives`() {
        assertFailsWith<IllegalArgumentException> { CAVODWeights(information = -1.0) }
    }

    @Test
    fun `explicit information and option values win`() {
        val withValues = PlannerInput(
            subject = "explicit",
            at = "2026-11-01T10:00:00+00:00",
            options = listOf(
                ActionOption(
                    "ask",
                    Verb.ASK,
                    "ask",
                    expectedBenefit = 0.5,
                    params = mapOf("decision_value" to mapOf("information_value" to 0.9)),
                ),
                ActionOption(
                    "wait",
                    Verb.WAIT,
                    "wait",
                    expectedBenefit = 0.1,
                    params = mapOf("decision_value" to mapOf("option_value" to 0.7)),
                ),
            ),
            attributes = mapOf("uncertainty" to 0.5),
        )

        val plan = CAVODPlanner().solve(withValues)

        assertEquals("ask", plan.actionId)
        assertEquals(0.9, plan.attributes["information_value"])
    }
}
