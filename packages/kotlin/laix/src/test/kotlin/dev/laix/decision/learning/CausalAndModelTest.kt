package dev.laix.decision.learning

import dev.laix.decision.learning.causal.CausalLedger
import dev.laix.decision.learning.model.ModelLearner
import dev.laix.decision.learning.model.Transition
import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.planners.mdp.valueIteration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class CausalAndModelTest {
    @Test
    fun `difference in means`() {
        val ledger = CausalLedger()
        ledger.add("d1", arm = "ask", outcome = 1.0)
        ledger.add("d2", arm = "ask", outcome = 1.0)
        ledger.add("d3", arm = "wait", outcome = 0.0)
        ledger.add("d4", arm = "wait", outcome = 0.0)

        val effect = ledger.effect("ask", "wait")

        assertEquals(1.0, effect.estimate)
        assertEquals("difference-in-means", effect.method)
        assertEquals(0.0, effect.standardError)
        assertEquals(1.0, effect.ciLow)
        assertEquals(1.0, effect.ciHigh)
    }

    @Test
    fun `inverse propensity weighting`() {
        val ledger = CausalLedger()
        ledger.add("d1", arm = "ask", outcome = 1.0, propensity = 0.5)
        ledger.add("d2", arm = "wait", outcome = 0.0, propensity = 0.5)

        val effect = ledger.effect("ask", "wait")

        assertEquals(2.0, effect.estimate)
        assertEquals("inverse-propensity", effect.method)
    }

    @Test
    fun `both arms are required`() {
        val ledger = CausalLedger()
        ledger.add("d1", arm = "ask", outcome = 1.0)

        assertFailsWith<IllegalArgumentException> { ledger.effect("ask", "wait") }
    }

    @Test
    fun `outcomes feed the ledger`() {
        val outcomes = listOf(
            Outcome(
                id = "o1",
                decisionId = "d1",
                metric = "time",
                before = 10.0,
                after = 4.0,
                delta = -6.0,
                label = "helped",
                direction = "lower-better",
            ),
            Outcome(
                id = "o2",
                decisionId = "d2",
                metric = "time",
                before = 10.0,
                after = 10.0,
                delta = 0.0,
                label = "neutral",
            ),
        )
        val ledger = CausalLedger.fromOutcomes(outcomes, mapOf("d1" to "ask", "d2" to "wait"))

        assertEquals(listOf(6.0, 0.0), ledger.records.map { it.outcome })
        assertEquals(6.0, ledger.effect("ask", "wait").estimate)
    }

    @Test
    fun `effect by context skips incomplete strata`() {
        val ledger = CausalLedger()
        ledger.add("d1", arm = "ask", outcome = 1.0, context = mapOf("stratum" to "east"))
        ledger.add("d2", arm = "wait", outcome = 0.0, context = mapOf("stratum" to "east"))
        ledger.add("d3", arm = "ask", outcome = 1.0, context = mapOf("stratum" to "west"))

        val effects = ledger.effectByContext("ask", "wait")

        assertEquals(listOf("east"), effects.keys.toList())
        assertEquals(1.0, effects.getValue("east").estimate)
    }

    @Test
    fun `propensity is validated`() {
        assertFailsWith<IllegalArgumentException> {
            CausalLedger().add("d1", arm = "ask", outcome = 1.0, propensity = 2.0)
        }
    }

    @Test
    fun `the learner estimates transitions and reward`() {
        val learner = ModelLearner(prior = 0.5)
        learner.observe("s0", "go", "s1", 1.0)
        learner.observe("s0", "go", "s1", 1.0)
        learner.observe("s0", "go", "s0", 0.0)

        assertEquals(mapOf("s0" to 0.375, "s1" to 0.625), learner.transitionProbabilities("s0", "go"))
        assertEquals(0.666667, learner.expectedReward("s0", "go"))
        assertEquals(3, learner.learned().first().count)
    }

    @Test
    fun `commit rolls back a worse model`() {
        val learner = ModelLearner(prior = 0.5)
        learner.observe("s0", "go", "s1", 1.0)
        val validation = listOf(Transition("s0", "go", "s1", 1.0))

        assertEquals(true, learner.commit(validation))
        val best = learner.bestScore()

        learner.observe("s0", "go", "s0", -1.0)
        assertEquals(false, learner.commit(validation))
        assertEquals(best, learner.bestScore())
        assertEquals(mapOf("s1" to 1.0), learner.transitionProbabilities("s0", "go"))
        assertEquals(false, learner.history.last().second)
    }

    @Test
    fun `snapshots round-trip`() {
        val learner = ModelLearner()
        learner.observe("s0", "go", "s1", 2.0)
        val snapshot = learner.snapshot()

        val restored = ModelLearner()
        restored.restore(snapshot)

        assertEquals(mapOf("s1" to 1.0), restored.transitionProbabilities("s0", "go"))
        assertEquals(2.0, restored.expectedReward("s0", "go"))
    }

    @Test
    fun `a learned model feeds the MDP planner`() {
        val learner = ModelLearner()
        learner.observe("s0", "go", "s1", 1.0)
        learner.observe("s1", "go", "s1", 2.0)
        val model = learner.toMdpModel(start = "s0", horizon = 2)

        assertEquals(2.8, valueIteration(model)["s0"])
    }

    @Test
    fun `empty learnings and bad priors are rejected`() {
        assertFailsWith<IllegalArgumentException> { ModelLearner(prior = -1.0) }
        assertFailsWith<IllegalArgumentException> { ModelLearner().toMdpModel() }
        assertTrue(ModelLearner().evaluate(emptyList()) == 0.0)
    }
}
