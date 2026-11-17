package dev.laix.decision.appkit.cli

import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.decisionAttributes
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import java.nio.file.Files
import java.nio.file.Path
import java.util.Locale
import kotlin.system.exitProcess

/** Small developer CLI: explain or lint a decision JSON file. */
fun main(args: Array<String>) {
    exitProcess(run(args.toList()))
}

fun run(args: List<String>): Int {
    if (args.isEmpty()) {
        System.err.println("usage: laix <explain|lint> PATH [--json]")
        return 2
    }
    val command = args[0]
    val positional = args.drop(1).filter { !it.startsWith("--") }
    if (positional.isEmpty()) {
        System.err.println("laix: a decision file path is required")
        return 2
    }
    val asJson = args.contains("--json")
    val decision = try {
        loadDecision(positional.first())
    } catch (exception: Exception) {
        System.err.println("laix: ${exception.message}")
        return 2
    }

    return when (command) {
        "explain" -> {
            println(if (asJson) explainJson(decision) else explainText(decision))
            0
        }
        "lint" -> {
            val warnings = lint(decision)
            if (warnings.isEmpty()) {
                println("ok")
                0
            } else {
                warnings.forEach { println("warning: $it") }
                1
            }
        }
        else -> {
            System.err.println("laix: unknown command '$command'")
            2
        }
    }
}

fun loadDecision(path: String): Decision {
    val payload = parseJsonObject(Files.readString(Path.of(path)))
    val decisionPayload = when (val nested = payload["decision"]) {
        is Map<*, *> -> nested.entries.associate { it.key.toString() to it.value }
        else -> payload
    }
    return Decision.fromMap(decisionPayload)
}

fun explainText(decision: Decision): String {
    val approval = if (decision.requiresApproval) "required" else "not required"
    val lines = mutableListOf(
        "decision: ${decision.decisionId.ifEmpty { "-" }}",
        "verb: ${decision.verb.value}",
        "reason: ${decision.reasonCode}",
        String.format(Locale.ROOT, "confidence: %.3f", decision.confidence),
        "action: ${decision.actionId ?: "-"}",
        "policy: ${decision.policyVersion.ifEmpty { "-" }}",
        "approval: $approval",
        "reversible: ${decision.reversible}",
        "trace: ${decision.traceId.ifEmpty { "-" }}",
    )
    decision.score?.let {
        lines += String.format(Locale.ROOT, "score: %.4f", it)
    }
    decision.supersedes?.let { lines += "supersedes: $it" }
    if (decision.revision != 0) lines += "revision: ${decision.revision}"
    lines += "rationale: ${decision.rationale}"
    return lines.joinToString("\n")
}

fun explainJson(decision: Decision): String =
    decisionAttributes(decision).toSortedMap().toJson(pretty = true)

fun lint(decision: Decision): List<String> {
    val warnings = mutableListOf<String>()
    if (decision.decisionId.isEmpty()) warnings += "missing decision_id"
    if (decision.traceId.isEmpty()) warnings += "missing trace_id"
    if (decision.policyVersion.isEmpty()) warnings += "missing policy_version"
    if (decision.requiresApproval && decision.verb == Verb.ACT) {
        warnings += "act requires approval; the host must supply an approver"
    }
    if (decision.score == null) {
        warnings += "no score; the reason code is policy-driven"
    }
    return warnings
}
