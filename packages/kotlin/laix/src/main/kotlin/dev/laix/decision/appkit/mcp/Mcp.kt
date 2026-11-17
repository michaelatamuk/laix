package dev.laix.decision.appkit.mcp

import dev.laix.decision.appkit.json.parseRequest
import dev.laix.decision.contract.PlannerPolicy
import dev.laix.decision.contracts.SCHEMA_VERSION
import dev.laix.decision.decide
import dev.laix.decision.planners.composite.LiveCompositePlanner
import dev.laix.decision.support.toJson

/**
 * MCP tool: answer one decision request and return the decision JSON.
 *
 * The transport is not ported yet; this is the tool payload the MCP server
 * would expose.
 */
fun decideTool(request: Map<String, Any?>, policy: String = "auto"): String {
    val parsed = parseRequest(request)
    val decisions = when (policy) {
        "auto" -> decide(parsed)
        "live" -> decide(parsed, PlannerPolicy(LiveCompositePlanner()))
        else -> throw IllegalArgumentException("policy must be 'auto' or 'live'")
    }
    return mapOf("decisions" to decisions.map { it.toMap() }).toJson(pretty = true)
}

/** The contract version the server would advertise. */
fun version(): String = SCHEMA_VERSION
