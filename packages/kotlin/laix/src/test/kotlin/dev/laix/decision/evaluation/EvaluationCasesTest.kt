package dev.laix.decision.evaluation

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.evaluation.cases.Case
import dev.laix.decision.evaluation.cases.benchmark
import dev.laix.decision.evaluation.cases.compare
import dev.laix.decision.evaluation.cases.compareSignalAttentionCase
import dev.laix.decision.evaluation.cases.loadCases
import dev.laix.decision.evaluation.cases.precisionRecall
import dev.laix.decision.evaluation.cases.runVectors
import dev.laix.decision.evaluation.cases.validateDocument
import dev.laix.decision.support.contractPath
import dev.laix.decision.support.toAny
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import java.nio.file.Files
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class EvaluationCasesTest {
    private fun document(name: String): Map<String, Any?> {
        @Suppress("UNCHECKED_CAST")
        return Json.parseToJsonElement(Files.readString(contractPath(name)))
            .jsonObject
            .toAny() as Map<String, Any?>
    }

    @Test
    fun `every attention vector passes`() {
        assertEquals(emptyList(), runVectors(document("signal-attention.v1.json")))
        assertEquals(emptyList(), validateDocument(document("signal-attention.v1.json")))
    }

    @Test
    fun `the validator catches a tampered case`() {
        val tampered = mapOf(
            "contract" to "laix",
            "version" to "1.1.0",
            "cases" to listOf(
                mapOf(
                    "id" to "broken",
                    "context" to mapOf("now" to "2026-11-01T10:00:00+02:00"),
                    "signals" to listOf(mapOf("id" to "s", "kind" to "k", "severity" to "high")),
                    "expected" to listOf(
                        mapOf(
                            "verb" to "notify_now",
                            "reason_code" to "worth_surfacing",
                            "deliver" to true,
                            "record" to true,
                            "score" to 1,
                        ),
                    ),
                ),
            ),
        )

        assertTrue(validateDocument(tampered).any { it.contains("unknown verb") })
    }

    @Test
    fun `a mismatched case is reported`() {
        val case = mapOf(
            "id" to "tampered",
            "context" to mapOf("now" to "2026-11-01T10:00:00+02:00", "quietHours" to null),
            "signals" to listOf(mapOf("id" to "s", "kind" to "k", "severity" to "high", "confidence" to 0.9)),
            "expected" to listOf(
                mapOf(
                    "verb" to "wait",
                    "reason_code" to "no",
                    "deliver" to false,
                    "record" to false,
                    "score" to 1,
                ),
            ),
        )

        val problems = compareSignalAttentionCase(case)

        assertTrue(problems.isNotEmpty())
        assertTrue(problems.first().contains("tampered"))
    }

    @Test
    fun `the attention bench beats both baselines`() {
        val report = benchmark(document("signal-attention-bench.v1.json"))
        @Suppress("UNCHECKED_CAST")
        val rows = report["rows"] as Map<String, Map<String, Any?>>

        val policyPrecision = rows.getValue("policy").getValue("precision") as Double
        val severityPrecision = rows.getValue("severity_only").getValue("precision") as Double
        val notifyPrecision = rows.getValue("always_notify").getValue("precision") as Double

        assertEquals(12, report["cases"])
        assertTrue(policyPrecision > severityPrecision)
        assertTrue(policyPrecision > notifyPrecision)
        assertEquals(0.0, rows.getValue("policy").getValue("hazard"))
        assertEquals(1.0, rows.getValue("always_notify").getValue("recall"))
    }

    @Test
    fun `generic precision and recall`() {
        val result = precisionRecall(listOf("a", "b"), listOf("b", "c"))

        assertEquals(2, result["detected"])
        assertEquals(2, result["known"])
        assertEquals(1, result["matched"])
        assertEquals(0.5, result["precision"])
        assertEquals(0.5, result["recall"])
        assertEquals(1.0, precisionRecall(emptyList(), emptyList())["precision"])
    }

    @Test
    fun `cases compare decisions field by field`() {
        val cases = listOf(
            Case(
                id = "one",
                request = mapOf("x" to 1),
                expected = listOf(
                    linkedMapOf(
                        "verb" to "act",
                        "reason_code" to "r",
                        "requires_approval" to false,
                    ),
                ),
            ),
        )
        val report = compare(cases, decide = {
            listOf(
                Decision(
                    verb = Verb.ACT,
                    confidence = 0.9,
                    reasonCode = "r",
                    rationale = "r",
                ),
            )
        })

        assertEquals(1, report.total)
        assertEquals(1, report.passed)
        assertEquals(1.0, report.agreementRate)
        assertEquals(1, (report.toMap()["rows"] as List<*>).size)
    }

    @Test
    fun `load cases reads the simple fixture`() {
        val cases = loadCases(
            mapOf(
                "cases" to listOf(
                    mapOf(
                        "id" to "c1",
                        "request" to mapOf("subject" to "s"),
                        "expected" to listOf(mapOf("verb" to "act")),
                    ),
                ),
            ),
        )

        assertEquals(1, cases.size)
        assertEquals("c1", cases.first().id)
        assertEquals(1, cases.first().expected.size)
    }
}
