package dev.laix.decision.appkit

import dev.laix.decision.appkit.mcp.McpStdioServer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.io.BufferedReader
import java.io.PrintWriter
import java.io.StringReader
import java.io.StringWriter
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class McpServerTest {
    private fun server(): McpStdioServer =
        McpStdioServer(BufferedReader(StringReader("")), PrintWriter(StringWriter()))

    private fun json(text: String) = Json.parseToJsonElement(text).jsonObject

    private fun call(name: String, arguments: Map<String, Any?>): String {
        val argumentsJson = dev.laix.decision.support.toJsonElement(arguments).toString()
        val line = """{"jsonrpc":"2.0","id":2,"method":"$name","params":$argumentsJson}"""
        return server().handle(line)!!
    }

    private fun decideArguments() = mapOf(
        "request" to mapOf(
            "subject" to "room-1",
            "at" to "2026-11-01T10:00:00+00:00",
            "situation" to mapOf("id" to "s-1"),
            "options" to listOf(
                mapOf("id" to "a-1", "verb" to "act", "name" to "assign_team", "expected_benefit" to 0.9),
            ),
            "attributes" to mapOf("urgency" to 0.9),
        ),
    )

    @Test
    fun `initialize returns server info`() {
        val response = json(
            server().handle(
                """{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}""",
            )!!,
        )
        val result = response.getValue("result").jsonObject

        assertEquals("2025-06-18", result.getValue("protocolVersion").jsonPrimitive.content)
        assertEquals("laix", result.getValue("serverInfo").jsonObject.getValue("name").jsonPrimitive.content)
    }

    @Test
    fun `notifications need no reply`() {
        assertNull(
            server().handle("""{"jsonrpc":"2.0","method":"notifications/initialized"}"""),
        )
    }

    @Test
    fun `tools list exposes decide`() {
        val response = json(
            server().handle("""{"jsonrpc":"2.0","id":3,"method":"tools/list"}""")!!,
        )
        val tools = response.getValue("result").jsonObject.getValue("tools").jsonArray

        assertEquals(1, tools.size)
        assertEquals("decide", tools.first().jsonObject.getValue("name").jsonPrimitive.content)
    }

    @Test
    fun `tools call answers a decision`() {
        val response = json(call("tools/call", mapOf("name" to "decide", "arguments" to decideArguments())))
        val result = response.getValue("result").jsonObject

        assertEquals(false, result.getValue("isError").jsonPrimitive.boolean)
        val text = result.getValue("content").jsonArray.first().jsonObject
            .getValue("text").jsonPrimitive.content
        val decisions = json(text).getValue("decisions").jsonArray
        assertEquals(1, decisions.size)
    }

    @Test
    fun `tools call reports tool errors`() {
        val response = json(
            call(
                "tools/call",
                mapOf(
                    "name" to "decide",
                    "arguments" to decideArguments() + mapOf("policy" to "custom"),
                ),
            ),
        )
        val result = response.getValue("result").jsonObject

        assertEquals(true, result.getValue("isError").jsonPrimitive.boolean)
    }

    @Test
    fun `invalid JSON and unknown methods are protocol errors`() {
        val parseError = json(server().handle("{not json")!!)
        assertEquals(-32700, parseError.getValue("error").jsonObject.getValue("code").jsonPrimitive.content.toInt())

        val unknown = json(server().handle("""{"jsonrpc":"2.0","id":4,"method":"missing"}""")!!)
        assertEquals(-32601, unknown.getValue("error").jsonObject.getValue("code").jsonPrimitive.content.toInt())
        assertTrue(unknown.containsKey("error"))
    }
}
