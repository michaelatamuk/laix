package dev.laix.decision.evaluation.cases

import dev.laix.decision.contracts.Decision
import dev.laix.decision.signals.SignalAttentionDecision
import dev.laix.decision.support.round

/** One parity fixture: a request and the decisions it should produce. */
data class Case(
    val id: String,
    val request: Any?,
    val expected: List<Map<String, Any?>> = emptyList(),
)

/** The compared result of one case. */
data class Row(
    val caseId: String,
    val expected: List<Map<String, Any?>>,
    val actual: List<Map<String, Any?>>,
    val mismatches: List<String>,
) {
    val passed: Boolean
        get() = mismatches.isEmpty()
}

/** The report a parity run returns. */
data class Report(
    val rows: List<Row> = emptyList(),
    val fields: List<String> = defaultFields,
) {
    val total: Int
        get() = rows.size

    val passed: Int
        get() = rows.count { it.passed }

    val failed: Int
        get() = total - passed

    val agreementRate: Double
        get() = if (total == 0) 1.0 else round(passed.toDouble() / total, 4)

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "cases" to total,
            "passed" to passed,
            "failed" to failed,
            "agreementRate" to agreementRate,
            "fields" to fields,
            "rows" to rows.map {
                linkedMapOf(
                    "case" to it.caseId,
                    "passed" to it.passed,
                    "mismatches" to it.mismatches,
                    "expected" to it.expected,
                    "actual" to it.actual,
                )
            },
        )

    companion object {
        val defaultFields: List<String> =
            listOf("verb", "reason_code", "deliver", "record", "requires_approval")
    }
}

/** Normalise any decision-like value into the flat comparison map. */
fun decisionMap(value: Any?): Map<String, Any?> =
    when (value) {
        is Decision -> value.toMap()
        is SignalAttentionDecision -> value.asDict()
        is Map<*, *> -> value.entries.associate { it.key.toString() to it.value }
        else -> emptyMap()
    }

/** Run one parity comparison over cases. */
fun compare(
    cases: List<Case>,
    decide: (Any?) -> List<Any?>,
    fields: List<String> = Report.defaultFields,
): Report {
    val rows = cases.map { case ->
        val actual = decide(case.request).map { decisionMap(it) }
        val problems = mutableListOf<String>()
        if (actual.size != case.expected.size) {
            problems += "decision count ${actual.size} != ${case.expected.size}"
        }
        for ((index, pair) in case.expected.zip(actual).withIndex()) {
            val (want, got) = pair
            for (name in fields) {
                if (want.containsKey(name) && want[name] != got[name]) {
                    problems += "item $index: $name ${got[name]} != ${want[name]}"
                }
            }
        }
        Row(
            caseId = case.id,
            expected = case.expected,
            actual = actual,
            mismatches = problems,
        )
    }
    return Report(rows, fields)
}

/** Read a simple JSON fixture: case -> request + expected decisions. */
fun loadCases(
    document: Map<String, Any?>,
    requestKey: String = "request",
    expectedKey: String = "expected",
): List<Case> {
    val cases = document["cases"] as? Iterable<*> ?: return emptyList()
    return cases.mapNotNull { item ->
        val map = (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
            ?: return@mapNotNull null
        Case(
            id = map["id"]?.toString() ?: "?",
            request = map[requestKey],
            expected = (map[expectedKey] as? Iterable<*>)?.mapNotNull { expected ->
                (expected as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
            } ?: emptyList(),
        )
    }
}
