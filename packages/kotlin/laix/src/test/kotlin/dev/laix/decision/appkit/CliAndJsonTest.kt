package dev.laix.decision.appkit

import dev.laix.decision.appkit.cli.explainJson
import dev.laix.decision.appkit.cli.explainText
import dev.laix.decision.appkit.cli.lint
import dev.laix.decision.appkit.cli.loadDecision
import dev.laix.decision.appkit.json.parseContext
import dev.laix.decision.appkit.json.parseOption
import dev.laix.decision.appkit.json.parseRequest
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.decide
import dev.laix.decision.support.parseJson
import dev.laix.decision.support.toJson
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class CliAndJsonTest {
    private val at = "2026-11-01T10:00:00+00:00"

    @Test
    fun `parses a full decision request`() {
        val request = parseRequest(
            mapOf(
                "subject" to "room-1",
                "at" to at,
                "situation" to mapOf(
                    "id" to "SIT-1",
                    "beliefs" to listOf(
                        mapOf("id" to "b1", "proposition" to "door open", "confidence" to 0.9),
                    ),
                    "constraints" to listOf(
                        mapOf("id" to "c1", "kind" to "risk", "value" to 0.5, "hard" to true),
                    ),
                    "attributes" to mapOf("urgency" to 0.9),
                ),
                "options" to listOf(
                    mapOf(
                        "id" to "a-1",
                        "verb" to "act",
                        "name" to "assign",
                        "expected_benefit" to 0.9,
                    ),
                ),
                "attributes" to mapOf("urgency" to 0.9),
                "target" to "some",
                "recipients" to listOf("ops"),
            ),
        )

        assertEquals("room-1", request.subject)
        assertEquals(1, request.options.size)
        assertEquals(Verb.ACT, request.options.first().verb)
        assertEquals(0.9, request.situation?.beliefs?.first()?.confidence)
        assertEquals(listOf("ops"), request.recipients)

        val decision = decide(request).single()
        assertEquals("a-1", decision.actionId)
    }

    @Test
    fun `parses signals and contexts`() {
        val request = parseRequest(
            mapOf(
                "subject" to "room-1",
                "at" to at,
                "signals" to listOf(
                    mapOf(
                        "id" to "s-1",
                        "kind" to "power",
                        "severity" to "high",
                        "confidence" to 0.9,
                        "intent" to mapOf("capability" to "act", "args" to mapOf("x" to 1)),
                    ),
                ),
                "context" to mapOf("now" to at),
            ),
        )

        assertEquals("s-1", request.signals.first().id)
        assertEquals("act", request.signals.first().intent?.capability)
        assertNotNull(request.context)
        val decision = decide(request).single()
        assertEquals(Verb.GUIDE, decision.verb)
    }

    @Test
    fun `a null quiet window means no quiet window`() {
        val context = parseContext(mapOf("now" to at, "quiet_hours" to null))
        assertNull(context.quietHours)

        val defaulted = parseContext(mapOf("now" to at))
        assertEquals("22:00", defaulted.quietHours?.start)
    }

    @Test
    fun `option parsing applies defaults`() {
        val option = parseOption(mapOf("id" to "a", "verb" to "wait", "name" to "wait"))

        assertEquals(0.5, option.expectedBenefit)
        assertEquals(true, option.reversible)
        assertEquals(0, option.latencyMs)
    }

    @Test
    fun `the CLI explains and lints a decision file`(@TempDir directory: Path) {
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.9,
            reasonCode = "policy_rule",
            rationale = "act",
            decisionId = "DEC-1",
            traceId = "TRC-1",
            policyVersion = "planner.v1",
            requiresApproval = true,
            score = 0.75,
        )
        val path = directory.resolve("decision.json")
        Files.writeString(path, decision.toJson(pretty = true))

        val loaded = loadDecision(path.toString())
        assertEquals(decision.decisionId, loaded.decisionId)
        assertTrue(explainText(loaded).contains("verb: act"))
        assertTrue(explainText(loaded).contains("approval: required"))
        assertEquals(
            listOf("act requires approval; the host must supply an approver"),
            lint(loaded),
        )
        @Suppress("UNCHECKED_CAST")
        val attributes = parseJson(explainJson(loaded)) as Map<String, Any?>
        assertEquals("act", attributes["laix.verb"])
        assertEquals(0.75, attributes["laix.score"])
    }

    @Test
    fun `the CLI accepts a decision record envelope`(@TempDir directory: Path) {
        val path = directory.resolve("record.json")
        Files.writeString(
            path,
            mapOf(
                "id" to "dr-1",
                "decision" to mapOf(
                    "verb" to "wait",
                    "confidence" to 0.5,
                    "reason_code" to "policy_rule",
                    "rationale" to "wait",
                    "decision_id" to "DEC-9",
                    "trace_id" to "TRC-9",
                    "policy_version" to "planner.v1",
                    "score" to 0.0,
                ),
            ).toJson(),
        )

        val loaded = loadDecision(path.toString())

        assertEquals("DEC-9", loaded.decisionId)
        assertEquals(emptyList(), lint(loaded))
    }
}
