package dev.laix.decision.planners.utility

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class UtilityPlannerTest {
    private fun problem(
        options: List<ActionOption>,
        constraints: List<Constraint> = emptyList(),
    ): PlannerInput =
        PlannerInput(
            subject = "choose",
            at = "2026-11-01T10:00:00Z",
            situation = Situation(
                id = "s-1",
                at = "2026-11-01T10:00:00Z",
                subject = "choose",
                constraints = constraints,
            ),
            options = options,
        )

    @Test
    fun `picks the highest feasible option`() {
        val result = UtilityPlanner().solve(
            problem(
                listOf(
                    ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
                    ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.6),
                ),
            ),
        )

        assertEquals("bold", result.actionId)
        assertEquals("expected_utility", result.reasonCode)
        assertEquals(0.75, result.score)
    }

    @Test
    fun `hard risk limit removes an option`() {
        val result = UtilityPlanner().solve(
            problem(
                listOf(
                    ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6, risk = 0.1),
                    ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.9),
                ),
                constraints = listOf(Constraint("risk", "risk", 0.5, hard = true)),
            ),
        )

        assertEquals("safe", result.actionId)
        assertTrue(result.alternatives.any { it["action_id"] == "bold" })
    }

    @Test
    fun `no options waits`() {
        val result = UtilityPlanner().solve(problem(emptyList()))

        assertEquals(Verb.WAIT, result.verb)
        assertEquals("no_options", result.reasonCode)
    }

    @Test
    fun `an averse model penalises risk more`() {
        val option = ActionOption("bold", Verb.ACT, "bold", expectedBenefit = 0.9, risk = 0.8)
        val neutral = UtilityModel().score(option)
        val averse = UtilityModel(riskAttitude = RiskAttitude.AVERSE).score(option)

        assertTrue(averse < neutral)
    }
}
