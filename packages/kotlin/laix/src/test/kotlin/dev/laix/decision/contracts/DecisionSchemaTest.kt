package dev.laix.decision.contracts

import com.fasterxml.jackson.databind.ObjectMapper
import com.networknt.schema.JsonSchemaFactory
import com.networknt.schema.SpecVersion
import dev.laix.decision.support.contractPath
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Validate the Kotlin JSON shape against the shared decision schema. */
class DecisionSchemaTest {
    private val mapper = ObjectMapper()
    private val schema = JsonSchemaFactory
        .getInstance(SpecVersion.VersionFlag.V202012)
        .getSchema(mapper.readTree(contractPath("decision.v1.schema.json").toFile()))

    private fun decisionJson(): String =
        Decision(
            verb = Verb.ASK,
            confidence = 0.82,
            reasonCode = "policy_rule",
            rationale = "ask first",
            decisionId = "DEC-1",
            situationId = "SIT-1",
            policyVersion = "planner.v1",
            actionId = "a-1",
            evidence = listOf(EvidenceRef(id = "e-1", kind = "document", quote = "quote")),
            breakdown = ScoreBreakdown(severity = 45.0, due = 20.0, confidence = 16.0, total = 81.0),
            intent = Intent("ask_user", mapOf("question" to "which one?")),
            alternatives = listOf(mapOf("action_id" to "a-2", "utility" to 0.3)),
            constraintsApplied = listOf("approval:human-required"),
            attributes = mapOf("urgency" to 0.5),
            traceId = "TRC-1",
        ).toJson()

    @Test
    fun `a serialized decision validates`() {
        val errors = schema.validate(mapper.readTree(decisionJson()))

        assertEquals(emptySet(), errors)
    }

    @Test
    fun `an invented verb fails validation`() {
        val payload = mapper.readTree(decisionJson()) as com.fasterxml.jackson.databind.node.ObjectNode
        payload.put("verb", "notify_now")

        val errors = schema.validate(payload)

        assertTrue(errors.isNotEmpty())
    }

    @Test
    fun `an extra property fails validation`() {
        val payload = mapper.readTree(decisionJson()) as com.fasterxml.jackson.databind.node.ObjectNode
        payload.put("surprise", true)

        val errors = schema.validate(payload)

        assertTrue(errors.isNotEmpty())
    }
}
