package dev.laix.decision.evaluation

import dev.laix.decision.evaluation.bench.HighestBenefitPlanner
import dev.laix.decision.evaluation.bench.FirstOptionPlanner
import dev.laix.decision.evaluation.bench.defaultCases
import dev.laix.decision.evaluation.bench.defaultPlanners
import dev.laix.decision.evaluation.bench.runLiveBench
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LiveBenchTest {
    @Test
    fun `default cases and planners are exposed`() {
        assertEquals(7, defaultCases().size)
        assertEquals(
            listOf("first", "benefit", "utility", "commitment", "execution", "attention", "live"),
            defaultPlanners().keys.toList(),
        )
    }

    @Test
    fun `the live planner wins every case`() {
        val report = runLiveBench()
        val live = report.metrics.first { it.planner == "live" }

        assertEquals(1.0, live.accuracy)
        assertEquals(0, live.safetyViolations)
        assertEquals(7, live.decisions)
        assertEquals(7, live.checked)
        assertEquals(7, report.cases.size)
        assertEquals(7, report.planners.size)
        assertEquals(49, report.rows.size)
    }

    @Test
    fun `metrics separate the baselines`() {
        val report = runLiveBench()
        val first = report.metrics.first { it.planner == "first" }
        val benefit = report.metrics.first { it.planner == "benefit" }

        assertTrue(first.accuracy < 1.0)
        assertTrue(benefit.accuracy < 1.0)
        assertTrue(first.meanScore != null)
        assertTrue(first.reasons.isNotEmpty())
    }

    @Test
    fun `the report serialises`() {
        val payload = runLiveBench().toMap()

        assertEquals(7, (payload["cases"] as List<*>).size)
        assertEquals(49, (payload["rows"] as List<*>).size)
        assertEquals(7, (payload["metrics"] as List<*>).size)
        assertTrue(runLiveBench().summary().contains("planner"))
    }

    @Test
    fun `custom baselines are accepted`() {
        val report = runLiveBench(
            cases = defaultCases(),
            planners = mapOf(
                "first" to FirstOptionPlanner(),
                "benefit" to HighestBenefitPlanner(),
            ),
        )

        assertEquals(2, report.metrics.size)
        assertEquals(14, report.rows.size)
    }
}
