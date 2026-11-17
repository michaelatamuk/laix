package dev.laix.decision.planners

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.commitment.CommitmentBeliefPlanner
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.commitment.CommitmentResolutionPlanner
import dev.laix.decision.planners.history.RevalidationPlanner
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class PlannersBatchTwoTest {
    private val supplier = CommitmentRef(owner = "supplier", ledger = "supplier", id = "c2")

    private fun graph(
        source: String = "reported",
        verifiedAt: String? = null,
    ): CommitmentGraph {
        val local = CommitmentLedger(
            listOf(
                Commitment(
                    id = "deliver",
                    subject = "deliver",
                    externalDependsOn = listOf(supplier),
                ),
            ),
        )
        val external = Commitment(
            id = "c2",
            subject = "ship",
            owner = "supplier",
            ledger = "supplier",
            status = "done",
            source = source,
            verifiedAt = verifiedAt,
        )
        return CommitmentGraph(local, listOf(external))
    }

    private fun problem(graph: CommitmentGraph): PlannerInput =
        PlannerInput(
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

    @Test
    fun `resolution proposes verification`() {
        val plan = CommitmentResolutionPlanner().solve(problem(graph()))

        assertEquals(Verb.VERIFY, plan.verb)
        assertEquals("commitment_resolution", plan.reasonCode)
        assertNotNull(plan.intent)
        assertEquals("verify_commitment", plan.intent?.capability)
        @Suppress("UNCHECKED_CAST")
        val refs = plan.attributes["verification_refs"] as List<Map<String, Any?>>
        assertEquals("c2", refs.first()["id"])

        val asked = CommitmentResolutionPlanner(mode = "ask").solve(problem(graph()))
        assertEquals(Verb.ASK, asked.verb)
        assertEquals(true, asked.requiresApproval)
    }

    @Test
    fun `resolution keeps a feasible plan`() {
        val plan = CommitmentResolutionPlanner().solve(
            problem(graph(source = "verified", verifiedAt = "2026-11-01T09:30:00+00:00")),
        )

        assertEquals("finish", plan.actionId)
    }

    @Test
    fun `resolution validates its mode`() {
        assertFailsWith<IllegalArgumentException> { CommitmentResolutionPlanner(mode = "silent") }
    }

    @Test
    fun `revalidation holds and revises`() {
        val fixedA = fixedPlanner("a")
        val fixedB = fixedPlanner("b")
        val options = listOf(ActionOption("a", Verb.ACT, "a"))

        val held = RevalidationPlanner(fixedA).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                options = options,
                attributes = mapOf("previous_action_id" to "a"),
            ),
        )
        assertEquals("decision_held", held.reasonCode)
        assertEquals("a", held.actionId)
        assertEquals(true, held.attributes["held"])

        val revised = RevalidationPlanner(fixedB).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                options = options,
                attributes = mapOf("previous_action_id" to "a"),
            ),
        )
        assertEquals("decision_revised", revised.reasonCode)
        assertEquals("b", revised.actionId)
    }

    @Test
    fun `revalidation escalates when the previous action is infeasible`() {
        val planner = object : Planner {
            override fun solve(problem: PlannerInput) = PlannerResult(
                verb = Verb.WAIT,
                confidence = 1.0,
                reasonCode = "no_feasible_option",
                rationale = "nothing works",
            )
        }

        val plan = RevalidationPlanner(planner).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                attributes = mapOf("previous_action_id" to "a"),
            ),
        )

        assertEquals(Verb.ESCALATE, plan.verb)
        assertEquals("decision_escalated", plan.reasonCode)
        assertEquals("a", plan.actionId)
    }

    @Test
    fun `revalidation marks a first run as new`() {
        val plan = RevalidationPlanner(fixedPlanner("a")).solve(
            PlannerInput(
                subject = "choose",
                at = "2026-11-01T10:00:00+00:00",
                options = listOf(ActionOption("a", Verb.ACT, "a")),
            ),
        )

        assertEquals("revalidated_new", plan.reasonCode)
        assertTrue(plan.attributes.containsKey("previous_action_id"))
    }

    @Test
    fun `belief planner verifies when the probability is low`() {
        val plan = CommitmentBeliefPlanner(defaultProbability = 0.4).solve(problem(graph()))

        assertEquals(Verb.VERIFY, plan.verb)
        assertEquals("commitment_belief_verify", plan.reasonCode)
        assertEquals(0.4, plan.attributes["completion_probability"])
    }

    @Test
    fun `belief planner acts when the probability is high`() {
        val input = problem(graph()).let {
            it.copy(
                attributes = it.attributes + mapOf(
                    "commitment_probabilities" to mapOf("supplier/supplier/c2" to 0.9),
                ),
            )
        }
        val plan = CommitmentBeliefPlanner(defaultProbability = 0.4).solve(input)

        assertEquals("finish", plan.actionId)
        assertEquals(0.9, plan.attributes["completion_probability"])
    }

    @Test
    fun `belief planner prefers a certain safe option`() {
        val input = PlannerInput(
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
                ActionOption("safe", Verb.ACT, "safe", expectedBenefit = 0.6),
            ),
            attributes = mapOf("commitment_graph" to graph()),
        )
        val plan = CommitmentBeliefPlanner(defaultProbability = 0.4).solve(input)

        assertEquals("safe", plan.actionId)
        assertEquals("commitment_belief", plan.reasonCode)
    }

    @Test
    fun `belief planner uses payload probabilities`() {
        val local = CommitmentLedger(
            listOf(
                Commitment(
                    id = "deliver",
                    subject = "deliver",
                    externalDependsOn = listOf(supplier),
                ),
            ),
        )
        val external = Commitment(
            id = "c2",
            subject = "ship",
            owner = "supplier",
            ledger = "supplier",
            status = "done",
            source = "reported",
            payload = mapOf("completion_probability" to 0.85),
        )
        val input = problem(CommitmentGraph(local, listOf(external)))

        val plan = CommitmentBeliefPlanner(defaultProbability = 0.4).solve(input)

        assertEquals("finish", plan.actionId)
        assertEquals(0.85, plan.attributes["completion_probability"])
    }

    @Test
    fun `belief planner rejects invalid settings`() {
        assertFailsWith<IllegalArgumentException> { CommitmentBeliefPlanner(defaultProbability = 2.0) }
        assertFailsWith<IllegalArgumentException> { CommitmentBeliefPlanner(verifyBelow = -1.0) }
    }

    private fun fixedPlanner(actionId: String) = object : Planner {
        override fun solve(problem: PlannerInput) = PlannerResult(
            verb = Verb.ACT,
            confidence = 1.0,
            reasonCode = "fixed",
            rationale = "fixed",
            actionId = actionId,
        )
    }

    @Test
    fun `the commitment planner still resolves blockers`() {
        val plan = CommitmentPlanner().solve(problem(graph()))
        assertEquals("wait", plan.actionId)
    }
}
