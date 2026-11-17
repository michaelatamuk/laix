package dev.laix.decision.evaluation.cases

import dev.laix.decision.contracts.Intent
import dev.laix.decision.signals.QuietHours
import dev.laix.decision.signals.Signal
import dev.laix.decision.signals.SignalContext
import dev.laix.decision.signals.SignalFeedback
import dev.laix.decision.signals.decideSignalAttention
import dev.laix.decision.support.parseIsoLocal
import dev.laix.decision.signals.rank
import dev.laix.decision.support.round
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.truthy
import java.nio.file.Files
import java.nio.file.Path
import kotlin.math.abs

private fun mapOfAny(value: Any?): Map<String, Any?>? =
    (value as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }

private fun strings(value: Any?): List<String> =
    (value as? Iterable<*>)?.map { it.toString() } ?: emptyList()

private fun bool(payload: Map<String, Any?>, key: String, default: Boolean): Boolean =
    payload[key]?.let { truthy(it) } ?: default

private fun number(payload: Map<String, Any?>, key: String, default: Double): Double =
    when (val value = payload[key]) {
        is Number -> value.toDouble()
        is String -> value.toDoubleOrNull() ?: default
        else -> default
    }

/** Build a signal context from the camelCase contract fixture shape. */
fun contextFrom(payload: Map<String, Any?>): SignalContext {
    val now = parseIsoLocal(payload["now"]?.toString())
        ?: throw IllegalArgumentException("a case context needs `now`")
    val feedback = mapOfAny(payload["feedback"])?.mapValues { (_, value) ->
        val entry = mapOfAny(value) ?: return@mapValues SignalFeedback(state = "")
        SignalFeedback(
            state = entry["state"]?.toString() ?: "",
            at = entry["at"]?.toString(),
            until = entry["until"]?.toString(),
            note = entry["note"]?.toString(),
        )
    } ?: emptyMap()
    val learned = mapOfAny(payload["learned"])?.mapValues {
        (it.value as? Number)?.toDouble() ?: 0.0
    } ?: emptyMap()
    return SignalContext(
        now = now,
        quietHours = QuietHours.parse(payload["quietHours"] ?: "22:00-06:00"),
        mode = payload["mode"]?.toString() ?: "shadow",
        stopped = bool(payload, "stopped", false),
        minSeverity = payload["minSeverity"]?.toString() ?: "high",
        minConfidence = number(payload, "minConfidence", 0.0),
        mutedKinds = strings(payload["mutedKinds"]),
        signalInterruptionBudget = (payload["signalInterruptionBudget"] as? Number)?.toInt(),
        sent = strings(payload["sent"]).toSet(),
        feedback = feedback,
        escalateAfterHours = (payload["escalateAfterHours"] as? Number)?.toDouble(),
        learned = learned,
        allowAct = bool(payload, "allowAct", false),
    )
}

/** Build a signal from the camelCase contract fixture shape. */
fun signalFrom(payload: Map<String, Any?>): Signal {
    fun intent(value: Any?): Intent? =
        mapOfAny(value)?.let {
            Intent(
                capability = it["capability"]?.toString() ?: "",
                args = mapOfAny(it["args"]) ?: emptyMap(),
            )
        }

    val escalation = mapOfAny(payload["escalation"])
    return Signal(
        id = payload["id"]?.toString() ?: "",
        kind = payload["kind"]?.toString() ?: "signal",
        title = payload["title"]?.toString() ?: "",
        detail = payload["detail"]?.toString() ?: "",
        severity = payload["severity"]?.toString() ?: "low",
        confidence = number(payload, "confidence", 0.5),
        due = payload["due"]?.toString(),
        evidenceRefs = strings(payload["evidenceRefs"]),
        groupKey = payload["groupKey"]?.toString(),
        interruptionCost = number(payload, "interruptionCost", 0.0),
        requiresApproval = bool(payload, "requiresApproval", false),
        intent = intent(payload["intent"]),
        reversible = bool(payload, "reversible", false),
        handover = escalation?.let {
            Intent(
                "handover",
                mapOf(
                    "target" to (it["target"]?.toString() ?: ""),
                    "reason" to (it["reason"]?.toString() ?: ""),
                ),
            )
        },
    )
}

private val FIELDS = listOf(
    "verb",
    "reason_code",
    "deliver",
    "record",
    "requires_approval",
    "score",
    "cost_of_waiting",
    "undo_hint",
    "reversible",
)

private fun equal(want: Any?, got: Any?): Boolean =
    when {
        want is Number && got is Number -> abs(want.toDouble() - got.toDouble()) < 1e-9
        else -> want == got
    }

/** Run one signal-attention case and return its decisions as maps. */
fun runCase(case: Map<String, Any?>): List<Map<String, Any?>> {
    val context = contextFrom(mapOfAny(case["context"]) ?: emptyMap())
    val signals = (case["signals"] as? Iterable<*>)?.mapNotNull { item ->
        mapOfAny(item)?.let { signalFrom(it) }
    } ?: emptyList()
    return decideSignalAttention(signals, context).map { it.asDict() }
}

/** Return mismatches for one case; empty means it passed. */
fun compareSignalAttentionCase(case: Map<String, Any?>): List<String> {
    val id = case["id"]?.toString() ?: "?"
    val expected = (case["expected"] as? Iterable<*>)?.mapNotNull { mapOfAny(it) } ?: emptyList()
    val actual = runCase(case)
    val problems = mutableListOf<String>()
    if (expected.size != actual.size) {
        problems += "$id: expected ${expected.size} decisions, got ${actual.size}"
        return problems
    }
    for ((index, pair) in expected.zip(actual).withIndex()) {
        val (want, got) = pair
        for (field in FIELDS) {
            if (want.containsKey(field) && !equal(want[field], got[field])) {
                problems += "$id A\u00b7 item $index: $field expected ${want[field]}, got ${got[field]}"
            }
        }
    }
    return problems
}

fun runVectors(document: Map<String, Any?>): List<String> {
    val cases = document["cases"] as? Iterable<*> ?: return emptyList()
    return cases.flatMap { item ->
        mapOfAny(item)?.let { compareSignalAttentionCase(it) } ?: emptyList()
    }
}

/** Read a fixture file and run its cases. */
fun loadVectors(path: Path): Map<String, Any?> = parseJsonObject(Files.readString(path))

/** Read a fixture file from its string path. */
fun loadVectors(path: String): Map<String, Any?> = loadVectors(Path.of(path))

/** Validate the fixture against the attention vocabulary. */
fun validateDocument(document: Map<String, Any?>): List<String> {
    val problems = mutableListOf<String>()
    if (document["contract"] != "laix") problems += "not a laix contract file"
    if (document["version"] == null) problems += "missing contract version"
    val cases = document["cases"] as? Iterable<*> ?: return problems + "cases must be a non-empty list"
    for (item in cases) {
        val case = mapOfAny(item) ?: continue
        val id = case["id"]?.toString() ?: "?"
        val context = mapOfAny(case["context"])
        if (context == null) {
            problems += "$id: missing context"
            continue
        }
        val signals = case["signals"] as? Iterable<*> ?: run {
            problems += "$id: signals must be a non-empty list"
            null
        } ?: continue
        val expected = case["expected"] as? Iterable<*> ?: run {
            problems += "$id: expected must have one decision per signal"
            null
        } ?: continue
        if (expected.count() != signals.count()) {
            problems += "$id: expected must have one decision per signal"
        }
        for (wantValue in expected) {
            val want = mapOfAny(wantValue) ?: continue
            val verb = want["verb"]?.toString()
            if (verb == null || dev.laix.decision.contracts.Verb.entries.none { it.value == verb }) {
                problems += "$id: unknown verb '$verb'"
            }
            val reason = want["reason_code"]?.toString()
            if (reason == null || reason !in dev.laix.decision.signals.REASONS) {
                problems += "$id: unknown reason '$reason'"
            }
            if (want["score"] !is Number) problems += "$id: expected score must be numeric"
            if (want["deliver"] !is Boolean) problems += "$id: expected deliver must be a boolean"
            if (want["record"] !is Boolean) problems += "$id: expected record must be a boolean"
        }
    }
    return problems
}

private val POLICIES = listOf("policy", "severity_only", "always_notify")

private fun delivers(name: String, signal: Signal, context: SignalContext): Boolean =
    when (name) {
        "always_notify" -> true
        "severity_only" -> rank(signal.severity) <= rank(context.minSeverity)
        else -> decideSignalAttention(listOf(signal), context).single().deliver
    }

/** Score the policy against two baselines on labelled cases. */
fun benchmark(document: Map<String, Any?>): Map<String, Any?> {
    val cases = document["cases"] as? Iterable<*> ?: emptyList<Any?>()
    val rows = LinkedHashMap<String, Map<String, Any?>>()
    for (name in POLICIES) {
        var raised = 0
        var helped = 0
        var harmful = 0
        var neutral = 0
        var missed = 0
        for (item in cases) {
            val case = mapOfAny(item) ?: continue
            val context = contextFrom(mapOfAny(case["context"]) ?: emptyMap())
            val signal = signalFrom(mapOfAny(case["signal"]) ?: emptyMap())
            val label = case["label"]?.toString() ?: "neutral"
            if (delivers(name, signal, context)) {
                raised++
                when (label) {
                    "helpful" -> helped++
                    "harmful" -> harmful++
                    else -> neutral++
                }
            } else if (label == "helpful") {
                missed++
            }
        }
        rows[name] = linkedMapOf(
            "raised" to raised,
            "helped" to helped,
            "harmful" to harmful,
            "neutral" to neutral,
            "missed_helpful" to missed,
            "precision" to if (raised > 0) round(helped.toDouble() / raised, 3) else 0.0,
            "hazard" to if (raised > 0) round(harmful.toDouble() / raised, 3) else 0.0,
            "recall" to if (helped + missed > 0) round(helped.toDouble() / (helped + missed), 3) else 0.0,
        )
    }
    return linkedMapOf(
        "contract" to "laix-bench",
        "version" to (document["version"] ?: ""),
        "cases" to cases.count(),
        "rows" to rows,
        "note" to (document["note"] ?: ""),
    )
}

/** Generic detection quality over past runs. */
fun precisionRecall(detected: Collection<String>, known: Collection<String>): Map<String, Any> {
    val detectedSet = detected.toSet()
    val knownSet = known.toSet()
    val matched = detectedSet.intersect(knownSet).size
    val precision = if (detectedSet.isNotEmpty()) matched.toDouble() / detectedSet.size else 1.0
    val recall = if (knownSet.isNotEmpty()) matched.toDouble() / knownSet.size else 1.0
    return linkedMapOf(
        "detected" to detectedSet.size,
        "known" to knownSet.size,
        "matched" to matched,
        "precision" to round(precision, 2),
        "recall" to round(recall, 2),
    )
}
