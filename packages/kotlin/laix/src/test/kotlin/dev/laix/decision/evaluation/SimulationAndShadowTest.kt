package dev.laix.decision.evaluation

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.evaluation.simulation.Scenario
import dev.laix.decision.evaluation.simulation.Simulator
import dev.laix.decision.evaluation.simulation.comparePlanners
import dev.laix.decision.evaluation.simulation.seededScenarios
import dev.laix.decision.planners.mdp.MDPPlanner
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.policies.ShadowPolicy
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import dev.laix.decision.policies.simulate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class SimulationAndShadowTest {
    private fun fixed(action: String) = object : Planner {
        override fun solve(problem: PlannerInput) = PlannerResult(
            verb = Verb.ACT,
            confidence = 1.0,
            reasonCode = "fixed",
            rationale = "always $action",
            actionId = action,
        )
    }

    private fun scenario(horizon: Int = 4) = Scenario(
        name = "left-or-right",
        simulator = Simulator(
            step = { state, action -> state to if (action == "right") 1.0 else 0.0 },
            actions = listOf("right", "wrong"),
            start = "s",
            horizon = horizon,
        ),
        optimum = horizon.toDouble(),
    )

    @Test
    fun `the simulator records each step`() {
        val result = scenario(2).run(fixed("right"))

        assertEquals(2.0, result.totalReward)
        assertEquals(2, result.steps.size)
        assertEquals("right", result.steps.first().action)
    }

    @Test
    fun `compare planners reports the best and the gap`() {
        val report = comparePlanners(
            mapOf("right" to fixed("right"), "wrong" to fixed("wrong")),
            listOf(scenario(4)),
        )
        val summary = report.summary()

        assertEquals("right", report.best())
        assertEquals(4.0, summary.getValue("right")["mean_reward"])
        assertEquals(0.0, summary.getValue("right")["mean_gap"])
        assertEquals(1.0, summary.getValue("wrong")["mean_gap"])
        assertTrue((report.toMap()["rows"] as List<*>).size == 2)
    }

    @Test
    fun `a simulator built from an MDP runs the planner`() {
        val model = MdpModel(
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
            horizon = 2,
        )

        val result = Simulator.fromMdp(model).run(MDPPlanner(model))

        assertEquals(3.0, result.totalReward)
        assertEquals(listOf("go", "go"), result.steps.map { it.action })
    }

    @Test
    fun `seeded scenarios are repeatable`() {
        val first = seededScenarios(7, count = 2, horizon = 3)
        val second = seededScenarios(7, count = 2, horizon = 3)

        assertEquals(first.map { it.name }, second.map { it.name })
        assertEquals(first.map { it.optimum }, second.map { it.optimum })
        val report = comparePlanners(mapOf("a" to fixed("a")), first)
        assertEquals("a", report.best())
    }

    @Test
    fun `seeded MDP simulation is repeatable`() {
        val model = MdpModel(
            states = listOf("s0", "s1", "s2"),
            actions = listOf("go"),
            transitions = listOf(
                MdpTransition("s0", "go", "s1", 0.5, 1.0),
                MdpTransition("s0", "go", "s2", 0.5, 2.0),
            ),
            start = "s0",
            horizon = 1,
        )
        val simulator = Simulator.fromMdp(model, seed = 7)

        val first = simulator.run(fixed("go"))
        val second = simulator.run(fixed("go"))

        assertEquals(first, second)
        assertTrue(first.finalState in setOf("s1", "s2"))
        val endings = (1..200).map {
            Simulator.fromMdp(model, seed = it).run(fixed("go")).finalState
        }.toSet()
        assertEquals(setOf("s1", "s2"), endings)
    }

    @Test
    fun `simulators validate their settings`() {
        assertFailsWith<IllegalArgumentException> {
            Simulator({ s, _ -> s to 0.0 }, emptyList(), start = "s")
        }
        assertFailsWith<IllegalArgumentException> {
            Simulator({ s, _ -> s to 0.0 }, listOf("a"), start = "s", horizon = -1)
        }
        assertFailsWith<IllegalArgumentException> { seededScenarios(1, count = 0) }
        assertFailsWith<IllegalArgumentException> { seededScenarios(1, horizon = 0) }
    }

    private fun request(amount: Int) = DecisionRequest(
        subject = "a task",
        at = "2026-11-01T10:00:00+00:00",
        attributes = mapOf("amount" to amount),
    )

    @Test
    fun `simulate runs a policy offline`() {
        val policy = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf("amount" to mapOf("gte" to 500)),
                    verb = Verb.ASK,
                    reasonCode = "over_limit",
                ),
            ),
        )

        val decisions = simulate(policy, listOf(request(100), request(700)))

        assertEquals(listOf(Verb.WAIT, Verb.ASK), decisions.map { it.first().verb })
    }

    @Test
    fun `a shadow policy returns the primary and records differences`() {
        val primary = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf("amount" to mapOf("gte" to 500)),
                    verb = Verb.ASK,
                    reasonCode = "over_limit",
                ),
            ),
        )
        val shadow = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf("amount" to mapOf("gte" to 500)),
                    verb = Verb.ACT,
                    reasonCode = "over_limit",
                ),
            ),
        )
        val policy = ShadowPolicy(primary, shadow)

        val decision = policy.decide(request(700)).first()

        assertEquals(Verb.ASK, decision.verb)
        assertEquals(1, policy.differences.size)
        assertEquals(Verb.ACT, policy.differences.first().shadow.first().verb)
    }
}
