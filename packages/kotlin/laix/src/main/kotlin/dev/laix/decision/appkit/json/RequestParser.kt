package dev.laix.decision.appkit.json

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Goal
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.SCHEMA_VERSION
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.TargetMode
import dev.laix.decision.contracts.Verb
import dev.laix.decision.signals.QuietHours
import dev.laix.decision.signals.Signal
import dev.laix.decision.signals.SignalContext
import dev.laix.decision.signals.SignalFeedback
import dev.laix.decision.support.parseIso
import dev.laix.decision.support.truthy

private fun mapOf(value: Any?): Map<String, Any?>? =
    (value as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }

private fun stringList(value: Any?): List<String> =
    (value as? Iterable<*>)?.map { it.toString() } ?: emptyList()

private fun text(payload: Map<String, Any?>, key: String, default: String = ""): String =
    payload[key]?.toString() ?: default

private fun number(payload: Map<String, Any?>, key: String, default: Double): Double =
    when (val value = payload[key]) {
        is Number -> value.toDouble()
        is String -> value.toDoubleOrNull() ?: default
        else -> default
    }

private fun bool(payload: Map<String, Any?>, key: String, default: Boolean): Boolean =
    payload[key]?.let { truthy(it) } ?: default

/** Build a [Situation] from its public JSON shape. */
fun parseSituation(payload: Map<String, Any?>, subject: String, at: String): Situation {
    val observations = (payload["observations"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let {
            Observation(
                id = text(it, "id"),
                at = text(it, "at", at),
                source = text(it, "source"),
                kind = text(it, "kind"),
                confidence = number(it, "confidence", 0.0),
                payload = mapOf(it["payload"]) ?: emptyMap(),
                cost = number(it, "cost", 0.0),
                latencyMs = number(it, "latency_ms", 0.0).toInt(),
                schemaVersion = text(it, "schema_version", SCHEMA_VERSION),
            )
        }
    } ?: emptyList()
    val beliefs = (payload["beliefs"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let {
            Belief(
                id = text(it, "id"),
                proposition = text(it, "proposition"),
                confidence = number(it, "confidence", 0.0),
                evidence = stringList(it["evidence"]),
                updatedAt = text(it, "updated_at"),
                expiresAt = it["expires_at"]?.toString(),
                source = text(it, "source", "observation"),
                schemaVersion = text(it, "schema_version", SCHEMA_VERSION),
            )
        }
    } ?: emptyList()
    val goals = (payload["goals"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let {
            Goal(
                id = text(it, "id"),
                statement = text(it, "statement"),
                priority = number(it, "priority", 0.5),
                metric = text(it, "metric"),
                target = (it["target"] as? Number)?.toDouble(),
                deadline = it["deadline"]?.toString(),
                schemaVersion = text(it, "schema_version", SCHEMA_VERSION),
            )
        }
    } ?: emptyList()
    val constraints = (payload["constraints"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let {
            Constraint(
                id = text(it, "id"),
                kind = text(it, "kind"),
                value = it["value"],
                hard = bool(it, "hard", true),
                statement = text(it, "statement"),
                schemaVersion = text(it, "schema_version", SCHEMA_VERSION),
            )
        }
    } ?: emptyList()
    return Situation(
        id = text(payload, "id", "situation-1"),
        at = text(payload, "at", at),
        subject = text(payload, "subject", subject),
        observations = observations,
        beliefs = beliefs,
        goals = goals,
        constraints = constraints,
        phase = text(payload, "phase", "observe"),
        horizon = text(payload, "horizon", "minutes"),
        attributes = mapOf(payload["attributes"]) ?: emptyMap(),
        schemaVersion = text(payload, "schema_version", SCHEMA_VERSION),
    )
}

/** Build an [ActionOption] from its public JSON shape. */
fun parseOption(payload: Map<String, Any?>): ActionOption =
    ActionOption(
        id = text(payload, "id"),
        verb = Verb.from(text(payload, "verb", Verb.ACT.value)),
        name = text(payload, "name"),
        params = mapOf(payload["params"]) ?: emptyMap(),
        expectedBenefit = number(payload, "expected_benefit", 0.5),
        cost = number(payload, "cost", 0.0),
        risk = number(payload, "risk", 0.0),
        latencyMs = number(payload, "latency_ms", 0.0).toInt(),
        interruptCost = number(payload, "interrupt_cost", 0.0),
        destructive = bool(payload, "destructive", false),
        reversible = bool(payload, "reversible", true),
        requiresApproval = bool(payload, "requires_approval", false),
        addresses = stringList(payload["addresses"]),
        rationale = text(payload, "rationale"),
        schemaVersion = text(payload, "schema_version", SCHEMA_VERSION),
    )

/** Build a [Signal] from its public JSON shape. */
fun parseSignal(payload: Map<String, Any?>): Signal {
    fun intent(value: Any?): Intent? =
        mapOf(value)?.let {
            Intent(
                capability = text(it, "capability"),
                args = mapOf(it["args"]) ?: emptyMap(),
            )
        }

    return Signal(
        id = text(payload, "id"),
        kind = text(payload, "kind", "signal"),
        title = text(payload, "title"),
        detail = text(payload, "detail"),
        severity = text(payload, "severity", "low"),
        confidence = number(payload, "confidence", 0.5),
        due = payload["due"]?.toString(),
        evidenceRefs = stringList(payload["evidence_refs"]),
        groupKey = payload["group_key"]?.toString(),
        interruptionCost = number(payload, "interruption_cost", 0.0),
        requiresApproval = bool(payload, "requires_approval", false),
        intent = intent(payload["intent"]),
        reversible = bool(payload, "reversible", false),
        handover = intent(payload["handover"]),
    )
}

/** Build a [SignalContext] from its public JSON shape. */
fun parseContext(payload: Map<String, Any?>): SignalContext {
    val now = parseIso(payload["now"]?.toString())
        ?: throw IllegalArgumentException("context.now is required")
    val quiet = if (payload.containsKey("quiet_hours")) {
        when (val raw = payload["quiet_hours"]) {
            null -> null
            is String -> QuietHours.parse(raw)
            is Iterable<*> -> QuietHours.parse(raw.toList())
            else -> null
        }
    } else {
        QuietHours("22:00", "06:00")
    }
    val feedback = mapOf(payload["feedback"])?.mapValues { (_, item) ->
        val entry = mapOf(item) ?: return@mapValues SignalFeedback(state = "")
        SignalFeedback(
            state = text(entry, "state"),
            at = entry["at"]?.toString(),
            until = entry["until"]?.toString(),
            note = entry["note"]?.toString(),
        )
    } ?: emptyMap()
    val learned = mapOf(payload["learned"])?.mapValues { (_, value) ->
        when (value) {
            is Number -> value.toDouble()
            is String -> value.toDoubleOrNull() ?: 0.0
            else -> 0.0
        }
    } ?: emptyMap()
    return SignalContext(
        now = now,
        quietHours = quiet,
        mode = text(payload, "mode", "shadow"),
        stopped = bool(payload, "stopped", false),
        minSeverity = text(payload, "min_severity", "high"),
        minConfidence = number(payload, "min_confidence", 0.0),
        mutedKinds = stringList(payload["muted_kinds"]),
        signalInterruptionBudget = (payload["signal_interruption_budget"] as? Number)?.toInt(),
        sent = stringList(payload["sent"]).toSet(),
        feedback = feedback,
        escalateAfterHours = (payload["escalate_after_hours"] as? Number)?.toDouble(),
        learned = learned,
        allowAct = bool(payload, "allow_act", false),
    )
}

/** Build a [DecisionRequest] from its public JSON shape. */
fun parseRequest(payload: Map<String, Any?>): DecisionRequest {
    val subject = text(payload, "subject").trim()
    val at = text(payload, "at").trim()
    require(subject.isNotEmpty()) { "request.subject is required" }
    require(at.isNotEmpty()) { "request.at is required" }

    val situation = mapOf(payload["situation"])?.let { parseSituation(it, subject, at) }
    val options = (payload["options"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let { parseOption(it) }
    } ?: emptyList()
    val signals = (payload["signals"] as? Iterable<*>)?.mapNotNull { item ->
        mapOf(item)?.let { parseSignal(it) }
    } ?: emptyList()
    val context = mapOf(payload["context"])?.let { parseContext(it) }
    val confidence = (payload["confidence"] as? Number)?.toDouble()
        ?: (payload["confidence"] as? String)?.toDoubleOrNull()

    return DecisionRequest(
        subject = subject,
        at = at,
        signals = signals,
        context = context,
        situation = situation,
        options = options,
        attributes = mapOf(payload["attributes"]) ?: emptyMap(),
        confidence = confidence,
        confidenceSource = text(payload, "confidence_source"),
        calibrated = bool(payload, "calibrated", false),
        deadline = payload["deadline"]?.toString(),
        validUntil = payload["valid_until"]?.toString(),
        eventId = text(payload, "event_id"),
        target = TargetMode.from(text(payload, "target", "one")),
        recipients = stringList(payload["recipients"]),
    )
}
