package dev.laix.decision.appkit

import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.execution.ExecutionStep
import dev.laix.decision.appkit.execution.Saga
import dev.laix.decision.appkit.execution.SagaStep
import dev.laix.decision.appkit.mcp.decideTool
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.parseJson
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class SagaMcpTest {
    private fun action(name: String) = ActionOption("a-$name", Verb.ACT, name)

    private fun requestOptions() = listOf(
        mapOf("id" to "a-1", "verb" to "act", "name" to "assign_team", "expected_benefit" to 0.9),
    )

    @Test
    fun `a saga compensates completed steps in reverse`() {
        val events = mutableListOf<String>()
        val compensated = mutableListOf<String>()
        val saga = Saga()

        val result = saga.run(
            listOf(
                SagaStep(
                    "first",
                    { events += "first"; emptyMap() },
                    { compensated += "first"; emptyMap() },
                ),
                SagaStep(
                    "second",
                    { events += "second"; emptyMap() },
                    { compensated += "second"; emptyMap() },
                ),
                SagaStep(
                    "third",
                    { error("boom") },
                ),
            ),
        )

        assertEquals(listOf("first", "second"), result.completed)
        assertEquals(listOf("second", "first"), result.compensated)
        assertTrue(result.error.orEmpty().contains("boom"))
        assertEquals(listOf("first", "second"), events)
        assertEquals(listOf("second", "first"), compensated)
    }

    @Test
    fun `run steps executes every step`() {
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "one" to { _: ActionOption, _: Map<String, Any?> -> mapOf("one" to true) },
                "two" to { _: ActionOption, _: Map<String, Any?> -> mapOf("two" to true) },
            ),
        )

        val result = bridge.runSteps(
            listOf(
                ExecutionStep(action("one")),
                ExecutionStep(action("two"), actor = "operator"),
            ),
        )

        assertEquals(listOf("one", "two"), result.completed)
        assertEquals(2, result.receipts.size)
        assertEquals(null, result.error)
        assertTrue(result.receipts.all { it.status == "executed" })
    }

    @Test
    fun `run steps compensates with undo handlers`() {
        val undone = mutableListOf<String>()
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "one" to { _: ActionOption, _: Map<String, Any?> -> mapOf("ok" to true) },
                "two" to { _: ActionOption, _: Map<String, Any?> -> error("boom") },
            ),
            undoHandlers = mapOf(
                "one" to { _: ActionOption, _: Map<String, Any?> ->
                    undone += "one"
                    mapOf("undone" to true)
                },
            ),
        )

        val result = bridge.runSteps(
            listOf(ExecutionStep(action("one")), ExecutionStep(action("two"))),
        )

        assertEquals(listOf("one"), result.completed)
        assertEquals(listOf("one"), result.compensated)
        assertEquals(listOf("one"), undone)
        assertTrue(result.error.orEmpty().contains("boom"))
    }

    @Test
    fun `run steps uses a custom compensation`() {
        var compensated = false
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "one" to { _: ActionOption, _: Map<String, Any?> -> emptyMap<String, Any?>() },
                "two" to { _: ActionOption, _: Map<String, Any?> -> error("boom") },
            ),
        )

        val result = bridge.runSteps(
            listOf(
                ExecutionStep(
                    action("one"),
                    compensate = {
                        compensated = true
                        mapOf("compensated" to true)
                    },
                ),
                ExecutionStep(action("two")),
            ),
        )

        assertEquals(true, compensated)
        assertEquals(listOf("one"), result.compensated)
    }

    @Test
    fun `the MCP tool answers auto and live requests`() {
        val auto = decideTool(
            mapOf(
                "subject" to "room-1",
                "at" to "2026-11-01T10:00:00+00:00",
                "situation" to mapOf("id" to "s-1"),
                "options" to requestOptions(),
                "attributes" to mapOf("urgency" to 0.9),
            ),
        )
        @Suppress("UNCHECKED_CAST")
        val autoPayload = parseJson(auto) as Map<String, Any?>
        assertEquals(1, (autoPayload["decisions"] as List<*>).size)

        val live = decideTool(
            mapOf(
                "subject" to "room-1",
                "at" to "2026-11-01T10:00:00+00:00",
                "situation" to mapOf("id" to "s-1"),
                "options" to requestOptions(),
                "attributes" to mapOf("urgency" to 0.9),
            ),
            policy = "live",
        )
        @Suppress("UNCHECKED_CAST")
        val livePayload = parseJson(live) as Map<String, Any?>
        @Suppress("UNCHECKED_CAST")
        val decision = (livePayload["decisions"] as List<Map<String, Any?>>).single()
        assertEquals("live_decision", decision["reason_code"])
    }

    @Test
    fun `the MCP tool validates the policy name`() {
        assertFailsWith<IllegalArgumentException> {
            decideTool(
                mapOf(
                    "subject" to "room-1",
                    "at" to "2026-11-01T10:00:00+00:00",
                    "situation" to mapOf("id" to "s-1"),
                ),
                policy = "custom",
            )
        }
    }
}
