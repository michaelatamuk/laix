package dev.laix.decision.planners

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.explain.CounterfactualVariable
import dev.laix.decision.planners.explain.commitmentVerificationCounterfactual
import dev.laix.decision.planners.explain.counterfactualSearch
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class CounterfactualSearchTest {
    @Test
    fun `search finds a rule threshold`() {
        val report = counterfactualSearch(
            decide = { values -> if (values.getValue("risk") >= 0.5) "escalate" else "act" },
            variables = listOf(
                CounterfactualVariable("risk", 0.4, 0.2, 0.8, step = 0.05),
            ),
            maxChanges = 1,
        )

        assertEquals("act", report.chosenId)
        assertEquals("escalate", report.counterfactualId)
        assertEquals("risk", report.changes.first().name)
        assertEquals(0.5, report.changes.first().new)
        assertEquals(0.1, report.distance, 1e-9)
    }

    @Test
    fun `search needs two changes`() {
        val report = counterfactualSearch(
            decide = { values ->
                if (values.getValue("risk") + values.getValue("uncertainty") >= 1.2) {
                    "escalate"
                } else {
                    "act"
                }
            },
            variables = listOf(
                CounterfactualVariable("risk", 0.4, 0.4, 0.7, step = 0.1),
                CounterfactualVariable("uncertainty", 0.2, 0.2, 0.5, step = 0.1),
            ),
            maxChanges = 2,
        )

        assertEquals("escalate", report.counterfactualId)
        assertEquals(setOf("risk", "uncertainty"), report.changes.map { it.name }.toSet())
        assertEquals(0.6, report.distance, 1e-9)
    }

    @Test
    fun `search returns no counterfactual when none flips`() {
        val report = counterfactualSearch(
            decide = { "act" },
            variables = listOf(
                CounterfactualVariable("risk", 0.4, 0.2, 0.8, step = 0.1),
            ),
            maxChanges = 1,
        )

        assertNull(report.counterfactualId)
        assertEquals(emptyList(), report.changes)
        assertEquals(0.0, report.distance)
    }

    @Test
    fun `search validates its settings`() {
        assertFailsWith<IllegalArgumentException> {
            counterfactualSearch({ "act" }, emptyList(), maxChanges = 0)
        }
        assertFailsWith<IllegalArgumentException> {
            counterfactualSearch({ "act" }, emptyList(), maxEvaluations = 0)
        }
        assertFailsWith<IllegalArgumentException> {
            counterfactualSearch(
                { "act" },
                listOf(CounterfactualVariable("x", 0.0, 0.0, 1.0, step = 0.0)),
            )
        }
        assertFailsWith<IllegalArgumentException> {
            counterfactualSearch(
                { "act" },
                listOf(CounterfactualVariable("x", 2.0, 0.0, 1.0)),
            )
        }
    }

    @Test
    fun `commitment verification shows the flip`() {
        val supplier = CommitmentRef(owner = "supplier", ledger = "supplier", id = "c2")
        val graph = CommitmentGraph(
            CommitmentLedger(
                listOf(
                    Commitment(
                        id = "deliver",
                        subject = "deliver",
                        externalDependsOn = listOf(supplier),
                    ),
                ),
            ),
            listOf(
                Commitment(
                    id = "c2",
                    subject = "ship",
                    owner = "supplier",
                    ledger = "supplier",
                    status = "done",
                    source = "reported",
                ),
            ),
        )
        val problem = PlannerInput(
            subject = "deliver",
            at = "2026-11-01T10:00:00+00:00",
            options = listOf(
                ActionOption(
                    "finish",
                    Verb.ACT,
                    "finish",
                    expectedBenefit = 1.0,
                    params = mapOf(
                        "commitments" to mapOf(
                            "fulfills" to listOf("deliver"),
                            "hard" to true,
                        ),
                    ),
                ),
                ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.1),
            ),
            attributes = mapOf("commitment_graph" to graph),
        )

        val result = commitmentVerificationCounterfactual(problem, CommitmentPlanner())

        assertEquals("wait", result.baseActionId)
        assertEquals(listOf("supplier/c2"), result.flips.map { it.name })
        assertEquals("finish", result.flips.first().counterfactualActionId)
        assertNotNull(result.flips.first())
    }
}
