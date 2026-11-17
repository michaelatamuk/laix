package dev.laix.decision.appkit

import dev.laix.decision.appkit.bench.Suite
import dev.laix.decision.appkit.bench.allSuites
import dev.laix.decision.appkit.bench.runBench
import dev.laix.decision.appkit.bench.runPlannerBench
import dev.laix.decision.appkit.bench.suiteNames
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class BenchTest {
    @Test
    fun `every bench suite passes`() {
        val report = runBench()

        assertEquals(1.0, report.agreement)
        assertEquals(0, report.failed)
        assertTrue(report.total >= 20)
        assertEquals(10, report.bySuite().size)
    }

    @Test
    fun `suites can be selected`() {
        val report = runBench(listOf("safety", "escalation"))

        assertEquals(1.0, report.agreement)
        assertEquals(setOf("safety", "escalation"), report.bySuite().keys)
        assertEquals(5, report.total)
    }

    @Test
    fun `suite names and descriptions are exposed`() {
        val names = suiteNames()
        val suites: List<Suite> = allSuites()

        assertEquals(10, names.size)
        assertEquals(names, suites.map { it.name })
        assertTrue(suites.all { it.description.isNotEmpty() })
        assertTrue(suites.all { it.cases.isNotEmpty() })
    }

    @Test
    fun `the report serialises`() {
        val payload = runBench(listOf("safety")).toMap()

        assertEquals(2, payload["total"])
        assertEquals(2, payload["passed"])
        assertEquals(1.0, payload["agreement"])
        assertTrue((payload["rows"] as List<*>).isNotEmpty())
    }

    @Test
    fun `unknown suites are rejected`() {
        assertFailsWith<IllegalArgumentException> { runBench(listOf("missing")) }
    }

    @Test
    fun `the planner bench prefers the MDP over the baseline`() {
        val report = runPlannerBench()
        val summary = report.summary()

        assertEquals("mdp", report.best())
        assertEquals(4.0, summary.getValue("mdp")["mean_reward"])
        assertEquals(0.0, summary.getValue("mdp")["mean_gap"])
        assertEquals(1.0, summary.getValue("stay-baseline")["mean_gap"])
    }
}
