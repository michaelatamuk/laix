package dev.laix.decision.planners

import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.planners.mdp.valueIteration
import dev.laix.decision.planners.pomdp.ObservationProbability
import dev.laix.decision.planners.pomdp.POMDPPlanner
import dev.laix.decision.planners.pomdp.PomdpModel
import dev.laix.decision.planners.pomdp.PomdpTransition
import dev.laix.decision.planners.pomdp.beliefEntropy
import dev.laix.decision.planners.pomdp.beliefFromState
import dev.laix.decision.planners.pomdp.beliefUpdate
import dev.laix.decision.planners.pomdp.comparePomdpToMdp
import dev.laix.decision.planners.pomdp.normalizeBelief
import dev.laix.decision.planners.pomdp.observationProbability
import dev.laix.decision.planners.pomdp.pomdpValue
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class PomdpTest {
    private fun model() = PomdpModel(
        states = listOf("s0", "s1"),
        actions = listOf("go", "stay"),
        observations = listOf("o0", "o1"),
        transitions = listOf(
            PomdpTransition("s0", "go", "s1", 1.0, 1.0),
            PomdpTransition("s0", "stay", "s0", 1.0, 0.0),
            PomdpTransition("s1", "go", "s1", 1.0, 2.0),
            PomdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        observationTable = listOf(
            ObservationProbability("s0", "go", "o0", 1.0),
            ObservationProbability("s0", "stay", "o0", 1.0),
            ObservationProbability("s1", "go", "o1", 1.0),
            ObservationProbability("s1", "stay", "o1", 1.0),
        ),
        discount = 0.9,
        horizon = 1,
    )

    @Test
    fun `belief from state and normalisation`() {
        assertEquals(mapOf("s0" to 1.0, "s1" to 0.0), beliefFromState("s0", listOf("s0", "s1")))
        assertEquals(
            mapOf("s0" to 0.5, "s1" to 0.5),
            normalizeBelief(mapOf("s0" to 2.0, "s1" to 2.0), listOf("s0", "s1")),
        )
        assertEquals(1.0, beliefEntropy(mapOf("s0" to 0.5, "s1" to 0.5)))
    }

    @Test
    fun `belief update uses the observation`() {
        val belief = beliefFromState("s0", listOf("s0", "s1"))
        val updated = beliefUpdate(model(), belief, "go", "o1")

        assertEquals(mapOf("s1" to 1.0), updated)
        assertEquals(1.0, observationProbability(model(), belief, "go", "o1"))
    }

    @Test
    fun `pomdp value and planner`() {
        val model = model()
        val belief = beliefFromState("s0", model.states)
        assertEquals(1.0, pomdpValue(model, belief))

        val plan = POMDPPlanner(model).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                attributes = mapOf("belief" to belief),
            ),
        )

        assertEquals(Verb.ACT, plan.verb)
        assertEquals("go", plan.actionId)
        assertEquals(1.0, plan.score)
        assertEquals(0.0, plan.attributes["entropy"])
    }

    @Test
    fun `the planner defaults to a uniform belief`() {
        val plan = POMDPPlanner(model()).solve(
            PlannerInput(subject = "choose", at = "2026-11-01T10:00:00+00:00"),
        )

        assertEquals("go", plan.actionId)
        assertEquals(mapOf("s0" to 0.5, "s1" to 0.5), plan.attributes["belief"])
    }

    @Test
    fun `the observation model is required`() {
        val error = assertFailsWith<IllegalArgumentException> {
            PomdpModel(
                states = listOf("s0", "s1"),
                actions = listOf("go"),
                observations = listOf("o0", "o1"),
                transitions = listOf(PomdpTransition("s0", "go", "s1", 1.0, 1.0)),
                observationTable = emptyList(),
            )
        }

        assertTrue(error.message.orEmpty().contains("missing observations"))
    }

    @Test
    fun `a fully observable pomdp matches the mdp path`() {
        val pomdp = model()
        val mdp = MdpModel(
            states = pomdp.states,
            actions = pomdp.actions,
            transitions = pomdp.transitions.map {
                MdpTransition(it.state, it.action, it.nextState, it.probability, it.reward)
            },
            start = "s0",
            discount = pomdp.discount,
            horizon = 2,
        )
        val belief = beliefFromState("s0", pomdp.states)
        val comparison = comparePomdpToMdp(pomdp, mdp, belief, horizon = 2)

        assertEquals("s0", comparison.state)
        assertEquals(comparison.mdp, comparison.pomdp)
        assertEquals(valueIteration(mdp)["s0"], comparison.pomdp)
        assertEquals(0.0, comparison.gap)
    }

    @Test
    fun `pomdp models validate their tables`() {
        assertFailsWith<IllegalArgumentException> {
            PomdpModel(
                states = listOf("s0"),
                actions = listOf("go"),
                observations = listOf("o0"),
                transitions = listOf(PomdpTransition("s0", "go", "s1", 1.0)),
                observationTable = emptyList(),
            )
        }
        assertFailsWith<IllegalArgumentException> {
            PomdpModel(
                states = listOf("s0"),
                actions = listOf("go"),
                observations = listOf("o0"),
                transitions = emptyList(),
                observationTable = listOf(
                    ObservationProbability("s0", "go", "missing", 1.0),
                ),
            )
        }
    }
}
