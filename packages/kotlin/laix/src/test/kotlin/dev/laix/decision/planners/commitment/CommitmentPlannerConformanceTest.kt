package dev.laix.decision.planners.commitment

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.contractPath
import dev.laix.decision.support.toAny
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.time.Duration
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull

/** Replays the shared commitment planner fixtures against this implementation. */
class CommitmentPlannerConformanceTest {
    private val json = Json

    private fun commitments(value: kotlinx.serialization.json.JsonArray): List<Commitment> =
        value.map { Commitment.fromMap(it.jsonObject.toAny() as Map<String, Any?>) }

    @Suppress("UNCHECKED_CAST")
    private fun options(value: kotlinx.serialization.json.JsonArray): List<ActionOption> =
        value.map { item ->
            val payload = item.jsonObject
            ActionOption(
                id = payload.getValue("id").jsonPrimitive.content,
                verb = Verb.from(payload.getValue("verb").jsonPrimitive.content),
                name = payload.getValue("name").jsonPrimitive.content,
                params = (payload["params"]?.toAny() as? Map<String, Any?>) ?: emptyMap(),
                expectedBenefit = (payload["expected_benefit"]?.jsonPrimitive?.content)
                    ?.toDoubleOrNull() ?: 0.5,
            )
        }

    @Test
    fun `every planner fixture case passes`() {
        val payload = json.parseToJsonElement(Files.readString(contractPath("commitment-graph.v1.json")))
            .jsonObject
        val cases = payload.getValue("planner_cases").jsonArray

        for (case in cases) {
            val fields = case.jsonObject
            val id = fields.getValue("id").jsonPrimitive.content
            val graph = CommitmentGraph(
                CommitmentLedger(commitments(fields.getValue("local").jsonArray)),
                commitments(fields.getValue("external").jsonArray),
            )
            val maxAge = fields["max_verification_age_seconds"]
                ?.jsonPrimitive
                ?.content
                ?.toDoubleOrNull()
                ?.let { Duration.ofMillis((it * 1000).toLong()) }
            val planner = CommitmentPlanner(
                requireVerified = fields.getValue("require_verified").jsonPrimitive.boolean,
                maxVerificationAge = maxAge,
            )

            val result = planner.solve(
                PlannerInput(
                    subject = "deliver",
                    at = "2026-11-01T10:00:00+00:00",
                    options = options(fields.getValue("options").jsonArray),
                    attributes = mapOf("commitment_graph" to graph),
                ),
            )

            val expectedAction = fields.getValue("expected_action_id").jsonPrimitive.content
            val expectedBlocked = fields.getValue("expected_blocked_by").jsonArray
                .map { it.jsonObject.toAny() }
            assertEquals(expectedAction, result.actionId, "$id action")

            if (result.actionId == "finish") {
                assertEquals(expectedBlocked, result.attributes["commitments_blocked_by"], "$id blocked_by")
            } else {
                val finish = result.alternatives.firstOrNull { it["action_id"] == "finish" }
                assertNotNull(finish, "$id has no finish alternative")
                assertEquals(expectedBlocked, finish["blocked_by"], "$id alternative blocked_by")
            }
        }
    }
}
