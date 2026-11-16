package dev.laix.decision.planners.commitment

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.InMemoryCommitmentStore
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

class CommitmentPlannerTest {
    private fun commitment(
        id: String,
        due: String? = null,
        priority: Double = 0.5,
        dependsOn: List<String> = emptyList(),
    ) = Commitment(id = id, subject = id, due = due, priority = priority, dependsOn = dependsOn)

    private fun problem(
        options: List<ActionOption>,
        commitments: List<Commitment>,
    ) = PlannerInput(
        subject = "deliver",
        at = "2026-11-01T10:00:00+00:00",
        options = options,
        attributes = mapOf("commitments" to CommitmentLedger(commitments)),
    )

    @Test
    fun `commitment effects are read from nested and flat params`() {
        val nested = commitmentEffect(
            ActionOption(
                "a",
                Verb.ACT,
                "a",
                params = mapOf(
                    "commitments" to mapOf(
                        "fulfills" to listOf("c1"),
                        "violates" to "c2",
                        "creates" to listOf(mapOf("id" to "c3")),
                        "hard" to true,
                    ),
                ),
            ),
        )
        assertEquals(listOf("c1"), nested.fulfills)
        assertEquals(listOf("c2"), nested.violates)
        assertEquals(listOf("c3"), nested.creates)
        assertEquals(true, nested.hard)

        val flat = commitmentEffect(
            ActionOption("b", Verb.ACT, "b", params = mapOf("fulfills" to "c1")),
        )
        assertEquals(listOf("c1"), flat.fulfills)
        assertEquals(emptyList(), flat.violates)
    }

    @Test
    fun `a hard violation is infeasible`() {
        val finish = ActionOption(
            "finish",
            Verb.ACT,
            "finish",
            expectedBenefit = 1.0,
            params = mapOf(
                "commitments" to mapOf("violates" to listOf("deliver"), "hard" to true),
            ),
        )
        val wait = ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.1)

        val result = CommitmentPlanner().solve(problem(listOf(finish, wait), listOf(commitment("deliver"))))

        assertEquals("wait", result.actionId)
        val rejected = result.alternatives.first { it["action_id"] == "finish" }
        assertEquals("blocked_hard_commitment", rejected["rejected_reason_code"])
        assertTrue((rejected["rejected_because"] as String).contains("hard commitment"))
    }

    @Test
    fun `fulfilling a due commitment wins a tie`() {
        val fulfill = ActionOption(
            "finish",
            Verb.ACT,
            "finish",
            expectedBenefit = 0.8,
            params = mapOf("commitments" to mapOf("fulfills" to listOf("deliver"))),
        )
        val ignore = ActionOption("ignore", Verb.ACT, "ignore", expectedBenefit = 0.8)

        val result = CommitmentPlanner(
            model = dev.laix.decision.planners.utility.UtilityModel(),
        ).solve(
            problem(
                listOf(ignore, fulfill),
                listOf(commitment("deliver", due = "2026-10-30T10:00:00+00:00", priority = 0.9)),
            ),
        )

        assertEquals("finish", result.actionId)
        assertEquals(listOf("deliver"), result.attributes["commitments_fulfilled"])
        assertEquals(listOf("deliver"), result.attributes["commitments_due_fulfilled"])
        assertTrue((result.score ?: 0.0) > 0.8)
    }

    @Test
    fun `a blocked dependency is reported with a stable code`() {
        val finish = ActionOption(
            "finish",
            Verb.ACT,
            "finish",
            expectedBenefit = 1.0,
            params = mapOf(
                "commitments" to mapOf("fulfills" to listOf("deliver"), "hard" to true),
            ),
        )
        val wait = ActionOption("wait", Verb.WAIT, "wait", expectedBenefit = 0.1)
        val graph = CommitmentGraph(
            CommitmentLedger(
                listOf(
                    commitment("deliver", dependsOn = listOf("ship")),
                    commitment("ship"),
                ),
            ),
        )
        val input = PlannerInput(
            subject = "deliver",
            at = "2026-11-01T10:00:00+00:00",
            options = listOf(finish, wait),
            attributes = mapOf("commitment_graph" to graph),
        )

        val result = CommitmentPlanner().solve(input)

        assertEquals("wait", result.actionId)
        val rejected = result.alternatives.first { it["action_id"] == "finish" }
        assertEquals("blocked_open_dependency", rejected["rejected_reason_code"])
        assertEquals(
            listOf(
                mapOf(
                    "owner" to "local",
                    "ledger" to null,
                    "id" to "ship",
                    "reason" to "open",
                ),
            ),
            rejected["blocked_by"],
        )
    }

    @Test
    fun `creating a new commitment costs points`() {
        val creates = ActionOption(
            "create",
            Verb.ACT,
            "create",
            expectedBenefit = 0.8,
            params = mapOf("commitments" to mapOf("creates" to listOf("new"))),
        )
        val plain = ActionOption("plain", Verb.ACT, "plain", expectedBenefit = 0.8)

        val result = CommitmentPlanner().solve(problem(listOf(creates, plain), emptyList()))

        assertEquals("plain", result.actionId)
        assertTrue(result.alternatives.any { it["action_id"] == "create" && it["commitment"] == -0.1 })
    }

    @Test
    fun `weights and ledger operations behave`() {
        assertFailsWith<IllegalArgumentException> { CommitmentWeights(keep = -1.0) }

        val ledger = CommitmentLedger(listOf(commitment("a"), commitment("b")))
        assertEquals(listOf("a", "b"), ledger.open().map { it.id })
        ledger.complete("a")
        assertNull(ledger.get("a")?.takeIf { it.status == "open" })
        assertEquals("cancelled", ledger.cancel("b").status)

        val store = InMemoryCommitmentStore()
        store.save("task-1", ledger)
        assertEquals(ledger.toMap(), store.load("task-1")?.toMap())
        store.delete("task-1")
        assertNull(store.load("task-1"))
    }
}
