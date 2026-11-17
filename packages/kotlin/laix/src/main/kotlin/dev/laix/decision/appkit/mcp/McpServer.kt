package dev.laix.decision.appkit.mcp

import dev.laix.decision.support.toJson
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonObject
import java.io.BufferedReader
import java.io.InputStream
import java.io.PrintWriter

const val MCP_PROTOCOL_VERSION: String = "2025-06-18"

/** Protocol revisions this server can speak. */
val MCP_SUPPORTED_PROTOCOL_VERSIONS: List<String> = listOf(
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
)

/**
 * Minimal MCP stdio server exposing the LAIX `decide` tool.
 *
 * Implements the JSON-RPC subset MCP needs: initialize, ping, tools/list and
 * tools/call.
 */
class McpStdioServer(
    private val input: BufferedReader,
    private val output: PrintWriter,
) {
    constructor(
        inputStream: InputStream = System.`in`,
        outputStream: java.io.OutputStream = System.out,
    ) : this(inputStream.bufferedReader(), PrintWriter(outputStream, true))

    fun run() {
        while (true) {
            val line = input.readLine() ?: break
            if (line.isBlank()) continue
            val response = handle(line)
            if (response != null) output.println(response)
        }
        output.flush()
    }

    /** Handle one JSON-RPC line; `null` means the message needs no reply. */
    fun handle(line: String): String? {
        val request: JsonObject = try {
            Json.parseToJsonElement(line).jsonObject
        } catch (exception: Exception) {
            return error(null, -32700, "Parse error: ${exception.message}")
        }
        val id = request["id"]
        val method = (request["method"] as? JsonPrimitive)?.content
            ?: return error(id, -32600, "Invalid request: missing method")
        if (id == null) return null  // notification

        return when (method) {
            "initialize" -> {
                // MCP negotiation: accept the client's revision when supported,
                // otherwise answer with the newest revision this server speaks.
                val requested = ((request["params"] as? JsonObject)?.get("protocolVersion")
                    as? JsonPrimitive)?.content
                val negotiated = requested
                    ?.takeIf { it in MCP_SUPPORTED_PROTOCOL_VERSIONS }
                    ?: MCP_PROTOCOL_VERSION
                result(
                    id,
                    linkedMapOf(
                        "protocolVersion" to negotiated,
                        "capabilities" to linkedMapOf("tools" to emptyMap<String, Any?>()),
                        "serverInfo" to linkedMapOf("name" to "laix", "version" to version()),
                    ),
                )
            }
            "ping" -> result(id, emptyMap<String, Any?>())
            "tools/list" -> result(id, linkedMapOf("tools" to listOf(toolDescriptor())))
            "tools/call" -> {
                val params = request["params"] as? JsonObject
                result(id, callTool(params))
            }
            else -> error(id, -32601, "Method not found: $method")
        }
    }

    private fun callTool(params: JsonObject?): Map<String, Any?> {
        val name = (params?.get("name") as? JsonPrimitive)?.content
            ?: return toolError("tools/call needs a tool name")
        if (name != "decide") return toolError("unknown tool: $name")
        val arguments = params["arguments"] as? JsonObject ?: JsonObject(emptyMap())
        val request = arguments["request"] as? JsonObject
            ?: return toolError("decide needs a request object")
        val policy = (arguments["policy"] as? JsonPrimitive)?.content ?: "auto"
        return try {
            val text = decideTool(rawMap(request), policy)
            linkedMapOf(
                "content" to listOf(linkedMapOf("type" to "text", "text" to text)),
                "isError" to false,
            )
        } catch (exception: Exception) {
            toolError("${exception::class.simpleName}: ${exception.message}")
        }
    }

    private fun toolError(message: String): Map<String, Any?> =
        linkedMapOf(
            "content" to listOf(linkedMapOf("type" to "text", "text" to message)),
            "isError" to true,
        )

    private fun toolDescriptor(): Map<String, Any?> =
        linkedMapOf(
            "name" to "decide",
            "title" to "Decide",
            "description" to (
                "Answer one LAIX decision request. Pass the public DecisionRequest JSON in `request`. " +
                    "Use `policy: auto` for decision dispatch or `policy: live` for the live composite " +
                    "planner. The result is a JSON array of Decision objects."
                ),
            "inputSchema" to linkedMapOf(
                "type" to "object",
                "properties" to linkedMapOf(
                    "request" to linkedMapOf("type" to "object"),
                    "policy" to linkedMapOf(
                        "type" to "string",
                        "enum" to listOf("auto", "live"),
                        "default" to "auto",
                    ),
                ),
                "required" to listOf("request"),
            ),
        )

    private fun result(id: JsonElement?, value: Map<String, Any?>): String =
        linkedMapOf<String, Any?>(
            "jsonrpc" to "2.0",
            "id" to id,
            "result" to value,
        ).toJson()

    private fun error(id: JsonElement?, code: Int, message: String): String =
        linkedMapOf<String, Any?>(
            "jsonrpc" to "2.0",
            "id" to id,
            "error" to linkedMapOf("code" to code, "message" to message),
        ).toJson()

    @Suppress("UNCHECKED_CAST")
    private fun rawMap(value: JsonObject): Map<String, Any?> =
        value.entries.associate { (key, item) -> key to rawValue(item) }

    private fun rawValue(value: JsonElement): Any? =
        when (value) {
            is JsonObject -> rawMap(value)
            is JsonArray -> value.map { rawValue(it) }
            is JsonPrimitive -> when {
                value.booleanOrNull != null -> value.booleanOrNull
                value.isString -> value.content
                value.content == "null" -> null
                else -> value.content.toLongOrNull() ?: value.content.toDoubleOrNull() ?: value.content
            }
        }
}
