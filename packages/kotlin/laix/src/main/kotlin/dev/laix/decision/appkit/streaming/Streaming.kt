package dev.laix.decision.appkit.streaming

import dev.laix.decision.appkit.records.Trace
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.DecisionStatus
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.iso
import dev.laix.decision.support.newId
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import dev.laix.decision.support.utcNow
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.time.Duration
import java.time.OffsetDateTime

/** Counters for one stream session. */
data class StreamStats(
    var observed: Int = 0,
    var decided: Int = 0,
    var late: Int = 0,
    var throttled: Int = 0,
    var dropped: Int = 0,
    var expired: Int = 0,
    var suppressed: Int = 0,
    var shed: Int = 0,
    var duplicates: Int = 0,
    var refineTimeouts: Int = 0,
    var provisional: Int = 0,
    var revised: Int = 0,
    var latencyP50: Double = 0.0,
    var latencyP95: Double = 0.0,
    var latencyP99: Double = 0.0,
) {
    fun snapshot(): Map<String, Any?> =
        linkedMapOf(
            "observed" to observed,
            "decided" to decided,
            "late" to late,
            "throttled" to throttled,
            "dropped" to dropped,
            "expired" to expired,
            "suppressed" to suppressed,
            "shed" to shed,
            "duplicates" to duplicates,
            "refine_timeouts" to refineTimeouts,
            "provisional" to provisional,
            "revised" to revised,
            "latency_p50" to latencyP50,
            "latency_p95" to latencyP95,
            "latency_p99" to latencyP99,
        )
}

/** A clock the caller moves. Used by replay and deterministic tests. */
class ManualClock(
    var now: OffsetDateTime = utcNow(),
) {
    operator fun invoke(): OffsetDateTime = now

    fun set(value: OffsetDateTime) {
        now = value
    }
}

/** Save, load and delete one stream snapshot. */
interface StreamCheckpointStore {
    fun save(key: String, snapshot: Map<String, Any?>)

    fun load(key: String): Map<String, Any?>?

    fun delete(key: String)
}

/** A process-local checkpoint store, useful in tests. */
class InMemoryStreamCheckpointStore : StreamCheckpointStore {
    private val items = LinkedHashMap<String, Map<String, Any?>>()

    override fun save(key: String, snapshot: Map<String, Any?>) {
        items[key] = snapshot
    }

    override fun load(key: String): Map<String, Any?>? = items[key]

    override fun delete(key: String) {
        items.remove(key)
    }
}

/** One JSON file per stream, under a host-owned directory. */
class FileStreamCheckpointStore(val directory: Path) : StreamCheckpointStore {
    init {
        Files.createDirectories(directory)
    }

    private fun path(key: String): Path {
        val safe = key.map { if (it in "/\\:*?\"<>|") '_' else it }.joinToString("")
        return directory.resolve("$safe.json")
    }

    override fun save(key: String, snapshot: Map<String, Any?>) {
        val target = path(key)
        val temporary = target.resolveSibling("${target.fileName}.tmp")
        Files.writeString(temporary, snapshot.toJson(pretty = true), Charsets.UTF_8)
        try {
            Files.move(
                temporary,
                target,
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE,
            )
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING)
        }
    }

    override fun load(key: String): Map<String, Any?>? {
        val target = path(key)
        if (!Files.exists(target)) return null
        return parseJsonObject(Files.readString(target))
    }

    override fun delete(key: String) {
        Files.deleteIfExists(path(key))
    }
}

/**
 * One live decision stream.
 *
 * Owns the state a live loop needs: an event-time watermark, a cooldown between
 * decisions, a bounded buffer with an explicit overflow policy, and revisions
 * that supersede an earlier decision.
 */
class StreamSession(
    private val decide: (DecisionRequest) -> List<Decision>,
    streamId: String = "",
    private val capacity: Int = 32,
    private val onFull: String = "latest_wins",
    private val late: String = "drop",
    private val cooldownMs: Long = 0,
    private val hysteresisMs: Long = 0,
    private val dedupeMs: Long = 0,
    private val maxDecisionsPerWindow: Int? = null,
    private val budgetWindowMs: Long = 1000,
    latencySamples: Int = 256,
    private val trace: Boolean = true,
    private val recorder: ((Decision) -> Unit)? = null,
    var humanAttentionBudget: HumanAttentionBudget? = null,
    var timeline: DecisionTimeline? = null,
    private var clock: () -> OffsetDateTime = { utcNow() },
    private val idFactory: () -> String = { newId("STR") },
) {
    init {
        require(capacity > 0) { "capacity must be positive" }
        require(onFull in FULL_POLICIES) { "unknown full policy: '$onFull'" }
        require(late in LATE_POLICIES) { "unknown late policy: '$late'" }
        require(cooldownMs >= 0) { "cooldown_ms must be zero or positive" }
        require(hysteresisMs >= 0) { "hysteresis_ms must be zero or positive" }
        require(dedupeMs >= 0) { "dedupe_ms must be zero or positive" }
        require(maxDecisionsPerWindow == null || maxDecisionsPerWindow > 0) {
            "max_decisions_per_window must be positive"
        }
        require(budgetWindowMs > 0) { "budget_window_ms must be positive" }
        require(latencySamples > 0) { "latency_samples must be positive" }
    }

    private val explicitStreamId: Boolean = streamId.isNotEmpty()
    var streamId: String = streamId.ifEmpty { idFactory() }
        private set

    private val latencySamplesLimit = latencySamples
    private val items = ArrayDeque<Decision>()
    private var closed = false
    private var watermark: OffsetDateTime? = null
    private var lastDecision: OffsetDateTime? = null
    private var lastSignature: List<Pair<String, String?>>? = null
    private var lastSignatureAt: OffsetDateTime? = null
    private var windowStart: OffsetDateTime? = null
    private var windowCount = 0
    private val latencies = ArrayDeque<Double>()
    private val seen = LinkedHashMap<String, OffsetDateTime>()
    private val traces = LinkedHashMap<String, Trace>()
    private val traceByDecision = LinkedHashMap<String, String>()
    private var stats = StreamStats()

    val isClosed: Boolean
        get() = closed

    val pending: Int
        get() = items.size

    fun stats(): StreamStats = stats.copy()

    /** Admit one event and return the decisions it produced. */
    fun observe(
        request: DecisionRequest,
        status: String = "final",
        force: Boolean = false,
    ): List<Decision> {
        val decisions = admit(request, status, force, revision = 0, supersedes = null)
        decisions.forEach { append(it) }
        return decisions
    }

    /** Decide again and mark the result as a revision of [previous]. */
    fun revise(
        previous: Decision,
        request: DecisionRequest,
        status: String = "final",
    ): List<Decision> {
        val decisions = admit(
            request,
            status,
            force = true,
            revision = previous.revision + 1,
            supersedes = previous.decisionId,
        )
        decisions.forEach { append(it) }
        return decisions
    }

    /** Push already-computed decisions as a revision of [previous]. */
    fun reviseWith(
        previous: Decision,
        request: DecisionRequest,
        decisions: List<Decision>,
        status: String = "final",
    ): List<Decision> {
        check(!closed) { "stream session is closed" }
        val decisionStatus = DecisionStatus.from(status)
        val revised = decisions.map {
            stamp(it, request, decisionStatus, previous.revision + 1, previous.decisionId)
        }
        if (revised.isNotEmpty()) {
            revised.forEach { append(it) }
            val now = clock()
            stats.decided += revised.size
            stats.revised += revised.size
            if (decisionStatus == DecisionStatus.PROVISIONAL) stats.provisional += revised.size
            lastDecision = now
            lastSignature = revised.map { it.verb.value to it.actionId }
            lastSignatureAt = now
            recordDecisions(revised)
        }
        return revised
    }

    /** Run a sequence with event time as the clock. */
    fun replay(requests: List<DecisionRequest>): List<Decision> {
        val original = clock
        val manual = ManualClock()
        clock = { manual() }
        val out = mutableListOf<Decision>()
        try {
            for (request in requests) {
                parseIso(request.at)?.let { manual.set(it) }
                out += admit(request, "final", force = false, revision = 0, supersedes = null, record = false)
            }
        } finally {
            clock = original
        }
        return out
    }

    fun save(store: StreamCheckpointStore, key: String) {
        store.save(key, snapshot())
    }

    fun resume(store: StreamCheckpointStore, key: String): Boolean {
        val snapshot = store.load(key) ?: return false
        restore(snapshot)
        return true
    }

    /** Return the resumable state, including pending decisions and traces. */
    fun snapshot(): Map<String, Any?> =
        linkedMapOf(
            "stream_id" to streamId,
            "watermark" to watermark?.toString(),
            "last_decision" to lastDecision?.toString(),
            "last_signature" to (lastSignature ?: emptyList<Pair<String, String?>>()).map {
                listOf(it.first, it.second)
            },
            "last_signature_at" to lastSignatureAt?.toString(),
            "window_start" to windowStart?.toString(),
            "window_count" to windowCount,
            "stats" to stats.snapshot(),
            "pending" to items.map { it.toMap() },
            "traces" to traces.values.map { it.toMap() },
            "timeline" to timeline?.toMap(),
            "human_attention_budget" to humanAttentionBudget?.toMap(),
        )

    /** Restore watermark, cadence, counters and buffered decisions. */
    fun restore(snapshot: Map<String, Any?>) {
        check(!closed) { "stream session is closed" }
        val snapshotId = snapshot["stream_id"]?.toString()
        if (!snapshotId.isNullOrEmpty()) {
            if (explicitStreamId && snapshotId != streamId) {
                throw IllegalArgumentException(
                    "checkpoint belongs to stream '$snapshotId', not '$streamId'",
                )
            }
            streamId = snapshotId
        }
        watermark = parseIso(snapshot["watermark"]?.toString())
        lastDecision = parseIso(snapshot["last_decision"]?.toString())
        lastSignature = (snapshot["last_signature"] as? Iterable<*>)?.mapNotNull { item ->
            (item as? Iterable<*>)?.toList()?.takeIf { it.size >= 2 }?.let {
                it[0].toString() to it[1]?.toString()
            }
        }
        lastSignatureAt = parseIso(snapshot["last_signature_at"]?.toString())
        windowStart = parseIso(snapshot["window_start"]?.toString())
        windowCount = (snapshot["window_count"] as? Number)?.toInt() ?: 0
        (snapshot["stats"] as? Map<*, *>)?.let { restoreStats(it) }
        (snapshot["pending"] as? Iterable<*>)?.let { pendingItems ->
            items.clear()
            for (item in pendingItems) {
                if (item is Map<*, *>) {
                    items.addLast(
                        Decision.fromMap(
                            item.entries.associate { it.key.toString() to it.value },
                        ),
                    )
                    if (items.size >= capacity) break
                }
            }
        }
        (snapshot["traces"] as? Iterable<*>)?.forEach { item ->
            (item as? Map<*, *>)?.let { map ->
                val trace = Trace(
                    id = map["id"]?.toString() ?: "",
                    decisionId = map["decision_id"]?.toString() ?: "",
                    createdAt = map["created_at"]?.toString() ?: iso(),
                    events = (map["events"] as? Iterable<*>)?.mapNotNull { event ->
                        (event as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                    } ?: emptyList(),
                    schemaVersion = map["schema_version"]?.toString()
                        ?: dev.laix.decision.contracts.SCHEMA_VERSION,
                )
                traces[trace.id] = trace
                traceByDecision[trace.decisionId] = trace.id
            }
        }
        (snapshot["human_attention_budget"] as? Map<*, *>)?.let {
            humanAttentionBudget = HumanAttentionBudget.fromMap(
                it.entries.associate { entry -> entry.key.toString() to entry.value },
            )
        }
        (snapshot["timeline"] as? Map<*, *>)?.let {
            timeline = DecisionTimeline.fromMap(
                it.entries.associate { entry -> entry.key.toString() to entry.value },
            )
        }
    }

    /** Stop accepting events; a consumer drains what is buffered. */
    fun close() {
        closed = true
    }

    /** Drain the buffer in FIFO order. */
    fun drain(): List<Decision> {
        val out = items.toList()
        items.clear()
        return out
    }

    fun trace(decisionId: String): Trace {
        val traceId = traceByDecision[decisionId]
            ?: throw NoSuchElementException("unknown decision '$decisionId'")
        return traces[traceId] ?: throw NoSuchElementException("unknown decision '$decisionId'")
    }

    private fun admit(
        request: DecisionRequest,
        status: String,
        force: Boolean,
        revision: Int,
        supersedes: String?,
        record: Boolean = true,
    ): List<Decision> {
        check(!closed) { "stream session is closed" }
        val decisionStatus = DecisionStatus.from(status)
        stats.observed++
        val now = clock()

        if (dedupeMs > 0 && request.eventId.isNotEmpty()) {
            purgeSeen(now)
            if (seen.containsKey(request.eventId)) {
                stats.duplicates++
                return emptyList()
            }
            seen[request.eventId] = now
        }

        parseIso(request.at)?.let { eventAt ->
            val mark = watermark
            if (mark != null && eventAt < mark) {
                if (late == "drop") {
                    stats.late++
                    return emptyList()
                }
            } else {
                watermark = eventAt
            }
        }

        val previousDecision = lastDecision
        if (!force && cooldownMs > 0 && previousDecision != null) {
            val elapsedMs = Duration.between(previousDecision, now).toMillis().toDouble()
            if (elapsedMs < cooldownMs) {
                stats.throttled++
                return emptyList()
            }
        }

        if (!force && !allowBudget(now)) return emptyList()

        val deadlineAt = parseIso(request.deadline)
        val expired = deadlineAt != null && now.toInstant().isAfter(deadlineAt.toInstant())
        val effectiveStatus = if (expired && decisionStatus == DecisionStatus.FINAL) {
            DecisionStatus.PROVISIONAL
        } else {
            decisionStatus
        }

        val started = System.nanoTime()
        val raw = decide(request)
        recordLatency((System.nanoTime() - started) / 1_000_000.0)
        val decisions = raw.map {
            stamp(it, request, effectiveStatus, revision, supersedes)
        }
        if (decisions.isEmpty()) return emptyList()

        val signature = decisions.map { it.verb.value to it.actionId }
        if (!force && hysteresisMs > 0 && lastSignature != null) {
            val signatureAt = lastSignatureAt
            val within = signatureAt != null &&
                Duration.between(signatureAt, now).toMillis() < hysteresisMs
            if (signature == lastSignature && within) {
                stats.suppressed += decisions.size
                lastDecision = now
                return emptyList()
            }
        }

        lastSignature = signature
        lastSignatureAt = now
        stats.decided += decisions.size
        if (effectiveStatus == DecisionStatus.PROVISIONAL) stats.provisional += decisions.size
        if (expired) stats.expired += decisions.size
        if (revision != 0) stats.revised += decisions.size
        lastDecision = now
        if (record) recordDecisions(decisions)
        return decisions
    }

    private fun purgeSeen(now: OffsetDateTime) {
        if (seen.isEmpty()) return
        val cutoff = now.minus(Duration.ofMillis(dedupeMs))
        val iterator = seen.iterator()
        while (iterator.hasNext()) {
            val entry = iterator.next()
            if (!entry.value.isAfter(cutoff) || seen.size > 4096) {
                iterator.remove()
            } else {
                return
            }
        }
    }

    private fun recordDecisions(decisions: List<Decision>) {
        for (decision in decisions) {
            if (trace && decision.traceId.isNotEmpty()) {
                val traceEntry = Trace(
                    id = decision.traceId,
                    decisionId = decision.decisionId,
                ).withEvent(
                    "decided",
                    linkedMapOf(
                        "verb" to decision.verb.value,
                        "reason_code" to decision.reasonCode,
                        "stream_id" to decision.streamId,
                        "event_time" to decision.eventTime,
                        "revision" to decision.revision,
                        "status" to decision.status.value,
                    ),
                )
                traces[decision.traceId] = traceEntry
                traceByDecision[decision.decisionId] = decision.traceId
            }
            recorder?.invoke(decision)
            timeline?.add(decision)
            humanAttentionBudget?.let { budget ->
                var cost = when (val raw = decision.attributes["human_attention_cost"]) {
                    is Number -> raw.toDouble()
                    is String -> raw.toDoubleOrNull() ?: 0.0
                    else -> 0.0
                }
                if (cost <= 0.0 && decision.requiresApproval) cost = 0.5
                budget.spend(cost)
            }
        }
    }

    private fun allowBudget(now: OffsetDateTime): Boolean {
        val cap = maxDecisionsPerWindow ?: return true
        val start = windowStart
        if (start == null ||
            Duration.between(start, now).toMillis() >= budgetWindowMs
        ) {
            windowStart = now
            windowCount = 0
        }
        if (windowCount >= cap) {
            stats.shed++
            return false
        }
        windowCount++
        return true
    }

    private fun recordLatency(elapsedMs: Double) {
        latencies.addLast(elapsedMs)
        while (latencies.size > latencySamplesLimit) latencies.removeFirst()
        val ordered = latencies.sorted()
        stats.latencyP50 = percentile(ordered, 50.0)
        stats.latencyP95 = percentile(ordered, 95.0)
        stats.latencyP99 = percentile(ordered, 99.0)
    }

    private fun percentile(ordered: List<Double>, percent: Double): Double {
        if (ordered.isEmpty()) return 0.0
        val index = kotlin.math.round((percent / 100.0) * (ordered.size - 1)).toInt()
        return kotlin.math.round(ordered[minOf(ordered.size - 1, maxOf(0, index))] * 1000) / 1000
    }

    private fun stamp(
        decision: Decision,
        request: DecisionRequest,
        status: DecisionStatus,
        revision: Int,
        supersedes: String?,
    ): Decision {
        var stamped = decision.copy(
            streamId = streamId,
            eventTime = request.at,
            deadline = request.deadline ?: decision.deadline,
            validUntil = request.validUntil ?: decision.validUntil,
            supersedes = supersedes ?: decision.supersedes,
            revision = maxOf(revision, decision.revision),
            status = status,
            target = request.target,
            recipients = request.recipients.ifEmpty { decision.recipients },
        )
        if (stamped.decisionId.isEmpty()) stamped = stamped.copy(decisionId = newId("DEC"))
        if (trace && stamped.traceId.isEmpty()) stamped = stamped.copy(traceId = newId("TRC"))
        return stamped
    }

    private fun append(decision: Decision) {
        if (closed) return
        if (items.size < capacity) {
            items.addLast(decision)
            return
        }
        when (onFull) {
            "drop_newest" -> stats.dropped++
            "drop_oldest" -> {
                items.removeFirst()
                stats.dropped++
                items.addLast(decision)
            }
            else -> {
                stats.dropped += items.size
                items.clear()
                items.addLast(decision)
            }
        }
    }

    private fun restoreStats(payload: Map<*, *>): Unit {
        fun int(key: String, default: Int = 0): Int =
            (payload[key] as? Number)?.toInt() ?: default
        fun double(key: String): Double =
            (payload[key] as? Number)?.toDouble() ?: 0.0
        stats = StreamStats(
            observed = int("observed"),
            decided = int("decided"),
            late = int("late"),
            throttled = int("throttled"),
            dropped = int("dropped"),
            expired = int("expired"),
            suppressed = int("suppressed"),
            shed = int("shed"),
            duplicates = int("duplicates"),
            refineTimeouts = int("refine_timeouts"),
            provisional = int("provisional"),
            revised = int("revised"),
            latencyP50 = double("latency_p50"),
            latencyP95 = double("latency_p95"),
            latencyP99 = double("latency_p99"),
        )
    }

    companion object {
        val FULL_POLICIES: List<String> = listOf("latest_wins", "drop_oldest", "drop_newest")
        val LATE_POLICIES: List<String> = listOf("drop", "accept")
    }
}

val FULL_POLICIES: List<String> = StreamSession.FULL_POLICIES
val LATE_POLICIES: List<String> = StreamSession.LATE_POLICIES
