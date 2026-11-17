package dev.laix.decision.planners

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.mdp.MDPPlanner
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.planners.mdp.actionValues
import dev.laix.decision.planners.mdp.planActions
import dev.laix.decision.planners.mdp.policyIteration
import dev.laix.decision.planners.mdp.valueIteration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class MdpTest {
    private fun model(horizon: Int? = 2) = MdpModel(
        states = listOf("s0", "s1", "s2"),
        actions = listOf("go", "stay"),
        transitions = listOf(
            MdpTransition("s0", "go", "s1", 1.0, 1.0),
            MdpTransition("s0", "stay", "s0", 1.0, 0.0),
            MdpTransition("s1", "go", "s2", 1.0, 2.0),
            MdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        start = "s0",
        discount = 0.9,
        horizon = horizon,
    )

    @Test
    fun `value iteration and action values`() {
        val values = valueIteration(model())

        assertEquals(0.0, values.getValue("s2"))
        assertEquals(2.0, values.getValue("s1"))
        assertEquals(2.8, values.getValue("s0"))
        assertEquals("go" to 2.8, actionValues(model(), "s0").first())
    }

    @Test
    fun `the planner returns the best action`() {
        val plan = MDPPlanner(model()).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                attributes = mapOf("state" to "s0"),
            ),
        )

        assertEquals(Verb.ACT, plan.verb)
        assertEquals("go", plan.actionId)
        assertEquals(2.8, plan.score)
        assertEquals("stay", plan.alternatives.first()["action_id"])
    }

    @Test
    fun `horizon limits lookahead`() {
        val plan = MDPPlanner(model(horizon = 1)).solve(
            PlannerInput(subject = "choose", at = "2026-11-01T10:00:00+00:00"),
        )

        assertEquals("go", plan.actionId)
        assertEquals(1.0, plan.score)
    }

    @Test
    fun `a terminal state waits`() {
        val plan = MDPPlanner(model()).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                attributes = mapOf("state" to "s2"),
            ),
        )

        assertEquals(Verb.WAIT, plan.verb)
        assertEquals("terminal_state", plan.reasonCode)
        assertEquals("s2", plan.attributes["state"])
    }

    @Test
    fun `greedy plan follows the value`() {
        assertEquals(listOf("s0:go", "s1:go"), planActions(model()))
    }

    @Test
    fun `transition probabilities must sum to one`() {
        val error = assertFailsWith<IllegalArgumentException> {
            MdpModel(
                states = listOf("s0", "s1"),
                actions = listOf("go"),
                transitions = listOf(
                    MdpTransition("s0", "go", "s0", 0.4, 0.0),
                    MdpTransition("s0", "go", "s1", 0.4, 0.0),
                ),
                start = "s0",
            )
        }
        assertTrue(error.message.orEmpty().contains("sum to"))
    }

    @Test
    fun `policy iteration matches the discounted model`() {
        val discounted = MdpModel(
            states = listOf("s0", "s1", "s2"),
            actions = listOf("go", "stay"),
            transitions = listOf(
                MdpTransition("s0", "go", "s1", 1.0, 1.0),
                MdpTransition("s0", "stay", "s0", 1.0, 0.0),
                MdpTransition("s1", "go", "s2", 1.0, 2.0),
                MdpTransition("s1", "stay", "s1", 1.0, 0.0),
            ),
            start = "s0",
            discount = 0.9,
            horizon = null,
        )

        val result = policyIteration(discounted)

        assertEquals("go", result.policy["s0"])
        assertEquals("go", result.policy["s1"])
        assertEquals(2.8, result.values["s0"]!!, 1e-6)
    }

    @Test
    fun `policy iteration needs an infinite horizon`() {
        assertFailsWith<IllegalArgumentException> { policyIteration(model()) }
    }

    @Test
    fun `models validate their states and actions`() {
        assertFailsWith<IllegalArgumentException> {
            MdpModel(listOf("s0", "s0"), listOf("go"), emptyList(), "s0")
        }
        assertFailsWith<IllegalArgumentException> {
            MdpModel(listOf("s0"), listOf("go"), emptyList(), "missing")
        }
        assertFailsWith<IllegalArgumentException> {
            MdpModel(
                listOf("s0", "s1"),
                listOf("go"),
                listOf(MdpTransition("s0", "go", "s1", 1.0)),
                start = "s0",
                discount = 2.0,
            )
        }
    }
}
