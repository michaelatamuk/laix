package dev.laix.decision.commitments

import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import dev.laix.decision.support.utcNow
import java.time.Duration
import java.time.OffsetDateTime

/** Why one commitment is blocked by another. */
data class CommitmentBlocker(
    val ref: CommitmentRef,
    val commitment: Commitment?,
    /** missing, open, unverified or stale */
    val reason: String,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "owner" to ref.owner,
            "ledger" to ref.ledger,
            "id" to ref.id,
            "reason" to reason,
        )
}

/** The structural problems found in one graph. */
data class CommitmentGraphReport(
    val missingRefs: List<CommitmentRef>,
    val cycles: List<List<CommitmentRef>>,
    val staleRefs: List<CommitmentRef> = emptyList(),
)

/**
 * A local ledger plus commitments owned by other parties.
 *
 * The graph never fetches remote state. The host resolves external
 * commitments and supplies them; the graph only reasons about the result.
 */
class CommitmentGraph(
    local: CommitmentLedger,
    external: List<Commitment> = emptyList(),
) {
    val local: CommitmentLedger = local
    val external: List<Commitment> = external.toList()

    private val items = LinkedHashMap<Triple<String, String, String>, Commitment>()

    init {
        for (commitment in this.local.all() + this.external) {
            val key = commitment.key
            require(!items.containsKey(key)) {
                "duplicate commitment '${commitment.id}' for owner '${commitment.owner}'"
            }
            items[key] = commitment
        }
    }

    constructor(
        local: List<Commitment>,
        external: List<Commitment> = emptyList(),
    ) : this(CommitmentLedger(local), external)

    /** Every commitment in the graph, sorted by owner, ledger and id. */
    val commitments: List<Commitment>
        get() = items.keys
            .sortedWith(compareBy({ it.first }, { it.second }, { it.third }))
            .map { items.getValue(it) }

    fun get(ref: CommitmentRef): Commitment? = items[ref.key]

    fun resolve(ref: CommitmentRef): Commitment? = get(ref)

    /** Local and external references that must be done before this one. */
    fun dependencies(commitment: Commitment): List<CommitmentRef> {
        val local = commitment.dependsOn.map { dependency ->
            CommitmentRef(owner = commitment.owner, ledger = commitment.ledger, id = dependency)
        }
        return local + commitment.externalDependsOn
    }

    /** Whether a promise is still within its verification window. */
    fun isFresh(commitment: Commitment, now: OffsetDateTime, maxAge: Duration): Boolean {
        if (commitment.source != "verified") return true
        val verified = parseIso(commitment.verifiedAt) ?: return false
        return Duration.between(verified, now) <= maxAge
    }

    /** Verified promises whose verification is older than [maxAge]. */
    fun staleRefs(now: OffsetDateTime, maxAge: Duration): List<CommitmentRef> =
        commitments
            .filter { !isFresh(it, now, maxAge) }
            .map { refFor(it) }
            .distinct()

    /** Return every dependency that still blocks this commitment. */
    fun blockers(
        commitment: Commitment,
        requireVerified: Boolean = false,
        now: OffsetDateTime? = null,
        maxVerificationAge: Duration? = null,
    ): List<CommitmentBlocker> {
        val found = mutableListOf<CommitmentBlocker>()
        val clock = if (maxVerificationAge != null) now ?: utcNow() else null
        for (ref in dependencies(commitment)) {
            val item = get(ref)
            when {
                item == null -> found += CommitmentBlocker(ref, null, "missing")
                item.status != "done" -> found += CommitmentBlocker(ref, item, "open")
                requireVerified && !item.trusted ->
                    found += CommitmentBlocker(ref, item, "unverified")
                requireVerified && maxVerificationAge != null && clock != null &&
                    !isFresh(item, clock, maxVerificationAge) ->
                    found += CommitmentBlocker(ref, item, "stale")
            }
        }
        return found
    }

    fun blocked(
        commitment: Commitment,
        requireVerified: Boolean = false,
        now: OffsetDateTime? = null,
        maxVerificationAge: Duration? = null,
    ): Boolean =
        blockers(commitment, requireVerified, now, maxVerificationAge).isNotEmpty()

    fun blockedOpen(
        requireVerified: Boolean = false,
        now: OffsetDateTime? = null,
        maxVerificationAge: Duration? = null,
    ): List<Commitment> =
        local.open().filter {
            blocked(it, requireVerified, now, maxVerificationAge)
        }

    /** Earliest open local commitment whose graph dependencies are done. */
    fun nextActionable(
        now: OffsetDateTime? = null,
        requireVerified: Boolean = false,
        maxVerificationAge: Duration? = null,
    ): Commitment? {
        val candidates = local.open().filter {
            !blocked(it, requireVerified, now, maxVerificationAge)
        }
        if (candidates.isEmpty()) return null
        return candidates
            .sortedWith(
                compareBy(
                    { parseIso(it.due) ?: OffsetDateTime.MAX },
                    { -it.priority },
                    { it.id },
                ),
            )
            .first()
    }

    /** References that do not resolve anywhere in the graph. */
    fun missingRefs(commitment: Commitment? = null): List<CommitmentRef> {
        val source = if (commitment != null) listOf(commitment) else commitments
        return source
            .flatMap { dependencies(it) }
            .filter { get(it) == null }
            .distinct()
    }

    /** Resolved dependencies that are reported but not verified. */
    fun unverifiedRefs(): List<CommitmentRef> =
        commitments
            .flatMap { dependencies(it) }
            .filter { ref -> get(ref)?.let { !it.trusted } ?: false }
            .distinct()

    /** Return missing references, cycles and stale verified promises. */
    fun validate(
        now: OffsetDateTime? = null,
        maxVerificationAge: Duration? = null,
    ): CommitmentGraphReport =
        CommitmentGraphReport(
            missingRefs = missingRefs(),
            cycles = cycles(),
            staleRefs = maxVerificationAge?.let { staleRefs(now ?: utcNow(), it) } ?: emptyList(),
        )

    /** Commitments this one depends on, directly or transitively. */
    fun ancestors(ref: CommitmentRef): List<Commitment> {
        val found = LinkedHashMap<Triple<String, String, String>, Commitment>()
        val seen = mutableSetOf(ref.key)
        val stack = ArrayDeque<CommitmentRef>()
        stack.addLast(ref)
        while (stack.isNotEmpty()) {
            val current = stack.removeLast()
            val item = get(current) ?: continue
            for (dependency in dependencies(item)) {
                if (dependency.key in seen) continue
                val child = get(dependency) ?: continue
                seen += dependency.key
                found[dependency.key] = child
                stack.addLast(dependency)
            }
        }
        return sorted(found)
    }

    /** Commitments that depend on this one, directly or transitively. */
    fun descendants(ref: CommitmentRef): List<Commitment> {
        val reverse = reverseIndex()
        val found = LinkedHashMap<Triple<String, String, String>, Commitment>()
        walkDescendants(ref.key, mutableSetOf(ref.key), reverse, found)
        return sorted(found)
    }

    /** Every decision affected if this commitment changes. */
    fun impact(ref: CommitmentRef): List<Commitment> = descendants(ref)

    /** The longest dependency chain that starts at this commitment. */
    fun chain(ref: CommitmentRef): List<Commitment> {
        val start = get(ref) ?: return emptyList()

        fun walk(item: Commitment, seen: Set<Triple<String, String, String>>): List<Commitment> {
            var best = listOf(item)
            for (dependency in dependencies(item)) {
                if (dependency.key in seen) continue
                val child = get(dependency) ?: continue
                val candidate = listOf(item) + walk(child, seen + dependency.key)
                if (candidate.size > best.size) best = candidate
            }
            return best
        }

        return walk(start, setOf(ref.key))
    }

    /** Longest dependency chain in the whole graph. */
    fun criticalPath(): List<Commitment> {
        var best = emptyList<Commitment>()
        for (item in commitments) {
            val path = chain(refFor(item))
            if (path.size > best.size) best = path
        }
        return best
    }

    /** Dependency cycles, each returned as its ordered references. */
    fun cycles(): List<List<CommitmentRef>> {
        val found = mutableListOf<List<CommitmentRef>>()
        val seen = mutableSetOf<List<Triple<String, String, String>>>()
        val complete = mutableSetOf<Triple<String, String, String>>()
        val stack = mutableListOf<Triple<String, String, String>>()

        fun walk(key: Triple<String, String, String>) {
            if (key in stack) {
                val start = stack.indexOf(key)
                val cycle = stack.drop(start) + key
                val canonical = cycle.distinct()
                    .sortedWith(compareBy({ it.first }, { it.second }, { it.third }))
                if (seen.add(canonical)) {
                    found += cycle.map { refForKey(it) }
                }
                return
            }
            if (key in complete) return
            val item = items[key] ?: return
            stack += key
            for (dependency in dependencies(item)) {
                walk(dependency.key)
            }
            stack.removeAt(stack.lastIndex)
            complete += key
        }

        for (key in items.keys) walk(key)
        return found
    }

    /** The induced subgraph for the supplied references. */
    fun subgraph(refs: Iterable<CommitmentRef>): CommitmentGraph {
        val keys = refs.map { it.key }.toSet()
        val local = CommitmentLedger(local.all().filter { it.key in keys })
        val external = external.filter { it.key in keys }
        return CommitmentGraph(local, external)
    }

    /** The commitment, its ancestors and its descendants. */
    fun neighborhood(ref: CommitmentRef): CommitmentGraph {
        val found = LinkedHashMap<Triple<String, String, String>, Commitment>()
        get(ref)?.let { found[it.key] = it }
        for (item in ancestors(ref) + descendants(ref)) {
            found[item.key] = item
        }
        return subgraph(found.values.map { refFor(it) })
    }

    /** A copy with every payload removed and, by default, every subject hidden. */
    fun redacted(keepSubject: Boolean = false): CommitmentGraph {
        fun clean(item: Commitment): Commitment =
            item.copy(
                subject = if (keepSubject) item.subject else "",
                payload = emptyMap(),
            )

        return CommitmentGraph(
            CommitmentLedger(local.all().map { clean(it) }),
            external.map { clean(it) },
        )
    }

    /** Render the graph as a Mermaid flowchart. */
    fun toMermaid(): String {
        val ids = commitments.withIndex().associate { (index, item) -> item.key to "n$index" }
        val lines = mutableListOf("flowchart LR")
        for (item in commitments) {
            val label = "${item.owner} · ${item.id} · ${item.subject} · ${item.status}"
                .replace('"', '\'')
                .replace("\n", " ")
            lines += "    ${ids.getValue(item.key)}[\"$label\"]"
        }
        for (item in commitments) {
            for (dependency in dependencies(item)) {
                val child = get(dependency) ?: continue
                val kind = if (dependency in localRefs(item)) "depends_on" else "external_depends_on"
                lines += "    ${ids.getValue(item.key)} -->|$kind| ${ids.getValue(child.key)}"
            }
        }
        return lines.joinToString("\n")
    }

    /** Render the graph as a Graphviz digraph. */
    fun toDot(): String {
        val ids = commitments.withIndex().associate { (index, item) -> item.key to "n$index" }
        val lines = mutableListOf("digraph commitments {")
        for (item in commitments) {
            val label = "${item.owner} · ${item.id} · ${item.subject} · ${item.status}"
                .replace("\"", "\\\"")
                .replace("\n", " ")
            lines += "  ${ids.getValue(item.key)} [label=\"$label\"];"
        }
        for (item in commitments) {
            for (dependency in dependencies(item)) {
                val child = get(dependency) ?: continue
                val kind = if (dependency in localRefs(item)) "depends_on" else "external_depends_on"
                lines += "  ${ids.getValue(item.key)} -> ${ids.getValue(child.key)} [label=\"$kind\"];"
            }
        }
        lines += "}"
        return lines.joinToString("\n")
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "local" to local.toMap(),
            "external" to external.map { it.toMap() },
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    private fun reverseIndex(): Map<Triple<String, String, String>, List<Commitment>> {
        val reverse = LinkedHashMap<Triple<String, String, String>, MutableList<Commitment>>()
        for (item in commitments) {
            for (dependency in dependencies(item)) {
                reverse.getOrPut(dependency.key) { mutableListOf() } += item
            }
        }
        return reverse
    }

    private fun walkDescendants(
        key: Triple<String, String, String>,
        seen: MutableSet<Triple<String, String, String>>,
        reverse: Map<Triple<String, String, String>, List<Commitment>>,
        found: MutableMap<Triple<String, String, String>, Commitment>,
    ) {
        for (item in reverse[key].orEmpty()) {
            if (item.key in seen) continue
            seen += item.key
            found[item.key] = item
            walkDescendants(item.key, seen, reverse, found)
        }
    }

    private fun sorted(
        found: Map<Triple<String, String, String>, Commitment>,
    ): List<Commitment> =
        found.keys
            .sortedWith(compareBy({ it.first }, { it.second }, { it.third }))
            .map { found.getValue(it) }

    private fun localRefs(commitment: Commitment): List<CommitmentRef> =
        commitment.dependsOn.map {
            CommitmentRef(owner = commitment.owner, ledger = commitment.ledger, id = it)
        }

    companion object {
        fun fromJson(text: String): CommitmentGraph = fromMap(parseJsonObject(text))

        fun refFor(commitment: Commitment): CommitmentRef =
            CommitmentRef(owner = commitment.owner, ledger = commitment.ledger, id = commitment.id)

        fun refForKey(key: Triple<String, String, String>): CommitmentRef =
            CommitmentRef(owner = key.first, ledger = key.second.ifEmpty { null }, id = key.third)

        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): CommitmentGraph {
            val localPayload = (payload["local"] as? Map<*, *>)?.entries?.associate { e ->
                e.key.toString() to e.value
            } ?: emptyMap()
            val external = (payload["external"] as? List<*>)
                ?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { e ->
                        e.key.toString() to e.value
                    }?.let { Commitment.fromMap(it) }
                } ?: emptyList()
            return CommitmentGraph(CommitmentLedger.fromMap(localPayload), external)
        }
    }
}
