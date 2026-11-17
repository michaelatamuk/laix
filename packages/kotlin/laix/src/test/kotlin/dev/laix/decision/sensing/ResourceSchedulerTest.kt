package dev.laix.decision.sensing

import dev.laix.decision.appkit.runtime.DecisionRuntime
import dev.laix.decision.sensing.resources.Budget
import dev.laix.decision.sensing.resources.ResourceScheduler
import dev.laix.decision.sensing.resources.SensingOption
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ResourceSchedulerTest {
    @Test
    fun `cheap detectors always run and deep calls need gain`() {
        val plan = ResourceScheduler().schedule(
            listOf(
                SensingOption("cheap-1", tier = "cheap", cost = 0.1),
                SensingOption("deep-1", tier = "deep", cost = 0.2, informationGain = 0.9),
                SensingOption("deep-2", tier = "deep", cost = 0.2, informationGain = 0.1),
            ),
            uncertainty = 0.8,
        )

        assertEquals(listOf("cheap-1", "deep-1"), plan.allowed)
        assertEquals(1, plan.deepCalls)
        assertEquals(0.3, plan.cost, 1e-9)
        assertTrue(plan.skipped.single()["reason"].toString().contains("below threshold"))
    }

    @Test
    fun `deep calls are bounded by calls cost and latency`() {
        val scheduler = ResourceScheduler(minInformationGain = 0.0)
        val noCalls = scheduler.schedule(
            listOf(SensingOption("deep", tier = "deep")),
            budget = Budget(maxDeepCalls = 0),
        )
        assertEquals(emptyList(), noCalls.allowed)
        assertEquals("deep-call budget exhausted", noCalls.skipped.single()["reason"])

        val noCost = scheduler.schedule(
            listOf(SensingOption("deep", tier = "deep", cost = 2.0)),
            budget = Budget(maxCost = 1.0),
        )
        assertEquals("cost budget exhausted", noCost.skipped.single()["reason"])

        val slow = scheduler.schedule(
            listOf(SensingOption("deep", tier = "deep", latencyMs = 5_000)),
            budget = Budget(maxLatencyMs = 2_000),
        )
        assertEquals("latency budget exceeded", slow.skipped.single()["reason"])
    }

    @Test
    fun `uncertainty weights the gain and is reported`() {
        val plan = ResourceScheduler(minInformationGain = 0.35).schedule(
            listOf(SensingOption("deep", tier = "deep", informationGain = 0.6)),
            uncertainty = 0.5,
        )

        assertEquals(emptyList(), plan.allowed)
        assertEquals(0.3, plan.skipped.single()["gain"])
        assertEquals(0.5, plan.attributes["uncertainty"])
    }

    @Test
    fun `sensing options are validated`() {
        kotlin.test.assertFailsWith<IllegalArgumentException> {
            SensingOption("bad", tier = "medium")
        }
        assertEquals(1.0, SensingOption("x", informationGain = 2.0).informationGain)
    }

    @Test
    fun `should escalate when confidence is low`() {
        assertTrue(ResourceScheduler.shouldEscalate(0.5))
        assertEquals(false, ResourceScheduler.shouldEscalate(0.9))
    }

    @Test
    fun `the runtime records resource plans`() {
        val runtime = DecisionRuntime()
        runtime.state.setBelief(
            dev.laix.decision.contracts.Belief(
                id = "b",
                proposition = "b",
                confidence = 0.2,
            ),
        )

        val plan = runtime.schedule(
            listOf(SensingOption("deep", tier = "deep", informationGain = 0.9)),
        )

        assertEquals(listOf("deep"), plan.allowed)
        assertTrue(runtime.state.history.any { it["event"] == "resource.plan" })
    }
}
