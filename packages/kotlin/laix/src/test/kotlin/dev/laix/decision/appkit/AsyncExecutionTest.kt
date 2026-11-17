package dev.laix.decision.appkit

import dev.laix.decision.appkit.execution.ApprovalRequired
import dev.laix.decision.appkit.execution.AsyncHandler
import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.execution.ExecutionStep
import dev.laix.decision.appkit.execution.RetryPolicy
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class AsyncExecutionTest {
    private fun action(name: String) = ActionOption("a-$name", Verb.ACT, name)

    private fun decision(requiresApproval: Boolean = false) = Decision(
        verb = Verb.ACT,
        confidence = 0.9,
        reasonCode = "policy_rule",
        rationale = "act",
        decisionId = "DEC-1",
        actionId = "assign_team",
        requiresApproval = requiresApproval,
    )

    @Test
    fun `async handlers execute`() = runBlocking {
        val assign: AsyncHandler = { _: ActionOption, _: Map<String, Any?> ->
            mapOf("assigned" to true)
        }
        val bridge = ExecutionBridge(asyncHandlers = mapOf("assign_team" to assign))

        val receipt = bridge.executeAsync(decision(), action("assign_team"), "operator")

        assertEquals("executed", receipt.status)
        assertEquals(true, receipt.detail["assigned"])
    }

    @Test
    fun `sync handlers run off the calling thread`() = runBlocking {
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> mapOf("ok" to true) },
            ),
        )

        val receipt = bridge.executeAsync(decision(), action("assign_team"), "operator")

        assertEquals("executed", receipt.status)
    }

    @Test
    fun `a timeout returns an unknown receipt`() = runBlocking {
        val slow: AsyncHandler = { _: ActionOption, _: Map<String, Any?> ->
            delay(2_000)
            mapOf("late" to true)
        }
        val bridge = ExecutionBridge(asyncHandlers = mapOf("assign_team" to slow))

        val receipt = bridge.executeAsync(
            decision(),
            action("assign_team"),
            "operator",
            timeoutSeconds = 0.05,
        )

        assertEquals("unknown", receipt.status)
        assertTrue(receipt.error.orEmpty().contains("TimeoutError"))
    }

    @Test
    fun `async retries recover`() = runBlocking {
        var attempts = 0
        val flaky: AsyncHandler = { _: ActionOption, _: Map<String, Any?> ->
            attempts++
            if (attempts < 2) error("boom") else mapOf("ok" to true)
        }
        val bridge = ExecutionBridge(asyncHandlers = mapOf("assign_team" to flaky))

        val receipt = bridge.executeAsync(
            decision(),
            action("assign_team"),
            "operator",
            retry = RetryPolicy(attempts = 2),
        )

        assertEquals("executed", receipt.status)
        assertEquals(2, receipt.detail["attempts"])
    }

    @Test
    fun `async execution still requires approval`() = runBlocking {
        val ok: AsyncHandler = { _: ActionOption, _: Map<String, Any?> -> emptyMap() }
        val bridge = ExecutionBridge(asyncHandlers = mapOf("assign_team" to ok))

        assertFailsWith<ApprovalRequired> {
            bridge.executeAsync(decision(requiresApproval = true), action("assign_team"), "operator")
        }
    }

    @Test
    fun `async run steps compensates completed work`() = runBlocking {
        val undone = mutableListOf<String>()
        val one: AsyncHandler = { _: ActionOption, _: Map<String, Any?> -> mapOf("ok" to true) }
        val two: AsyncHandler = { _: ActionOption, _: Map<String, Any?> -> error("boom") }
        val bridge = ExecutionBridge(
            asyncHandlers = mapOf("one" to one, "two" to two),
            undoHandlers = mapOf(
                "one" to { _: ActionOption, _: Map<String, Any?> ->
                    undone += "one"
                    mapOf("undone" to true)
                },
            ),
        )

        val result = bridge.runStepsAsync(
            listOf(ExecutionStep(action("one")), ExecutionStep(action("two"))),
        )

        assertEquals(listOf("one"), result.completed)
        assertEquals(listOf("one"), result.compensated)
        assertEquals(listOf("one"), undone)
        assertTrue(result.error.orEmpty().contains("boom"))
    }

    @Test
    fun `async timeouts are rejected as settings`() {
        assertFailsWith<IllegalArgumentException> {
            runBlocking {
                ExecutionBridge().executeAsync(
                    decision(),
                    action("assign_team"),
                    "operator",
                    timeoutSeconds = 0.0,
                )
            }
        }
    }
}
