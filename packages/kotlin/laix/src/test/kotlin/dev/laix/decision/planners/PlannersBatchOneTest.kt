package dev.laix.decision.planners

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.casebased.CaseBasedPlanner
import dev.laix.decision.planners.casebased.PastDecision
import dev.laix.decision.planners.conflict.ConflictResolutionPlanner
import dev.laix.decision.planners.portfolio.PortfolioPlanner
import dev.laix.decision.planners.portfolio.PlannerSelector
import dev.laix.decision.planners.risk.RiskBoundedPlanner
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class PlannersBatchOneTest {
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
    fun `risk bounded rejects the downside`() {
        val plan = RiskBoundedPlanner(maxLoss = 0.5).solve(
            problem(
                listOf(
                    ActionOption(
                        "safe",
                        Verb.ACT,
                        "safe",
                        expectedBenefit = 0.6,
                        params = mapOf("risk_bound" to mapOf("cvar_loss" to 0.1)),
                    ),
                    ActionOption(
                        "risky",
                        Verb.ACT,
                        "risky",
                        expectedBenefit = 1.0,
                        params = mapOf("risk_bound" to mapOf("cvar_loss" to 0.9)),
                    ),
                ),
            ),
        )

        assertEquals("safe", plan.actionId)
        assertEquals(0.1, plan.attributes["cvar_loss"])
        val risky = plan.alternatives.first { it["action_id"] == "risky" }
        assertEquals("risk_limit", risky["rejected_reason_code"])
    }

    @Test
    fun `risk bounded waits when everything exceeds the limit`() {
        val plan = RiskBoundedPlanner(maxLoss = 0.05).solve(
            problem(
                listOf(
                    ActionOption(
                        "risky",
                        Verb.ACT,
                        "risky",
                        params = mapOf("risk_bound" to mapOf("cvar_loss" to 0.9)),
                    ),
                ),
            ),
        )

        assertEquals(Verb.WAIT, plan.verb)
        assertEquals("no_feasible_option", plan.reasonCode)
        assertEquals(0.05, plan.attributes["risk_limit"])
    }

    @Test
    fun `risk bounded rejects negative settings`() {
        assertFailsWith<IllegalArgumentException> { RiskBoundedPlanner(maxLoss = -1.0) }
        assertFailsWith<IllegalArgumentException> { RiskBoundedPlanner(penalty = -1.0) }
    }

    @Test
    fun `conflict resolution escalates or resolves`() {
        val escalating = problem(
            listOf(ActionOption("a", Verb.ACT, "a")),
            mapOf(
                "goal_conflicts" to listOf(
                    mapOf("id" to "g1", "left" to "speed", "right" to "safety", "severity" to 0.9),
                ),
            ),
        )
        assertEquals(Verb.ESCALATE, ConflictResolutionPlanner().solve(escalating).verb)

        val resolving = problem(
            listOf(
                ActionOption(
                    "balanced",
                    Verb.ACT,
                    "balanced",
                    params = mapOf("resolves" to listOf("g1")),
                ),
            ),
            mapOf("goal_conflicts" to listOf(mapOf("id" to "g1", "severity" to 0.9))),
        )
        val plan = ConflictResolutionPlanner().solve(resolving)
        assertEquals("balanced", plan.actionId)
        assertEquals("goal_conflict_resolved", plan.reasonCode)
    }

    @Test
    fun `conflict resolution asks when severity is below escalation`() {
        val asking = problem(
            listOf(ActionOption("a", Verb.ACT, "a")),
            mapOf("goal_conflicts" to listOf(mapOf("id" to "g1", "severity" to 0.6))),
        )

        assertEquals(Verb.ASK, ConflictResolutionPlanner().solve(asking).verb)
    }

    @Test
    fun `conflict resolution delegates without a conflict`() {
        val fallback = object : Planner {
            override fun solve(problem: PlannerInput) = PlannerResult(
                verb = Verb.GUIDE,
                confidence = 1.0,
                reasonCode = "fixed",
                rationale = "fixed",
            )
        }

        assertEquals(
            "fixed",
            ConflictResolutionPlanner(fallback).solve(problem(emptyList())).reasonCode,
        )
        assertEquals(
            "no_goal_conflict",
            ConflictResolutionPlanner().solve(problem(emptyList())).reasonCode,
        )
    }

    @Test
    fun `case based reuses a similar case`() {
        val planner = CaseBasedPlanner(
            listOf(PastDecision(subject = "send the report", actionId = "send-now")),
        )
        val plan = planner.solve(
            PlannerInput(
                subject = "send the report today",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(
                    ActionOption("send-now", Verb.ACT, "send now"),
                    ActionOption("send-later", Verb.WAIT, "send later"),
                ),
            ),
        )

        assertEquals("send-now", plan.actionId)
        assertEquals("case_based", plan.reasonCode)
        assertTrue(plan.confidence > 0.5)
    }

    @Test
    fun `case based falls back without a close case`() {
        val planner = CaseBasedPlanner(
            listOf(PastDecision(subject = "unrelated subject", actionId = "other")),
            threshold = 0.9,
        )
        val plan = planner.solve(
            problem(listOf(ActionOption("a", Verb.ACT, "a"))).copy(subject = "something else"),
        )

        assertEquals("no_case", plan.reasonCode)
    }

    @Test
    fun `portfolio selects a planner and reports it`() {
        fun fixed(actionId: String) = object : Planner {
            override fun solve(problem: PlannerInput) = PlannerResult(
                verb = Verb.ACT,
                confidence = 1.0,
                reasonCode = "fixed",
                rationale = "fixed",
                actionId = actionId,
            )
        }

        val portfolio = PortfolioPlanner(
            mapOf("a" to fixed("a"), "b" to fixed("b")),
            selector = PlannerSelector { problem ->
                problem.attributes["planner"]?.toString() ?: "a"
            },
        )
        val result = portfolio.solve(
            problem(
                listOf(ActionOption("a", Verb.ACT, "a"), ActionOption("b", Verb.ACT, "b")),
                mapOf("planner" to "b"),
            ),
        )

        assertEquals("b", result.actionId)
        assertEquals("b", result.attributes["planner"])
        assertEquals(listOf("a", "b"), result.attributes["portfolio"])
    }

    @Test
    fun `the default selector routes by request shape`() {
        assertEquals(
            "commitment",
            PortfolioPlanner.defaultSelector(
                problem(
                    listOf(ActionOption("a", Verb.ACT, "a")),
                    mapOf("commitments" to listOf(mapOf("id" to "c1"))),
                ),
            ),
        )
        assertEquals(
            "execution",
            PortfolioPlanner.defaultSelector(
                problem(listOf(ActionOption("a", Verb.ACT, "a", destructive = true))),
            ),
        )
        assertEquals(
            "utility",
            PortfolioPlanner.defaultSelector(problem(listOf(ActionOption("a", Verb.ACT, "a")))),
        )
    }

    @Test
    fun `portfolio validates its default`() {
        val fixed = object : Planner {
            override fun solve(problem: PlannerInput) = PlannerResult(
                verb = Verb.WAIT,
                confidence = 1.0,
                reasonCode = "fixed",
                rationale = "fixed",
            )
        }

        assertFailsWith<IllegalArgumentException> {
            PortfolioPlanner(emptyMap())
        }
        assertFailsWith<IllegalArgumentException> {
            PortfolioPlanner(mapOf("a" to fixed), default = "missing")
        }
        assertNotNull(PortfolioPlanner(mapOf("a" to fixed)).solve(problem(emptyList())))
    }
}
