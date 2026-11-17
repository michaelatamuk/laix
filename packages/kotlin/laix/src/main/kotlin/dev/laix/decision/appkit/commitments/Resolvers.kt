package dev.laix.decision.appkit.commitments

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef

/**
 * Resolve owner-qualified references from host-managed state.
 *
 * The port is synchronous on purpose: LAIX never performs network I/O while
 * planning. A host with a remote source resolves into a local cache first and
 * serves this call from there.
 */
fun interface CommitmentResolver {
    fun resolve(refs: List<CommitmentRef>): List<Commitment>
}

/** An async variant for hosts that fetch before planning. */
interface AsyncCommitmentResolver {
    suspend fun resolve(refs: List<CommitmentRef>): List<Commitment>
}

/** Resolve from commitments already held by the host. */
class InMemoryCommitmentResolver(
    commitments: List<Commitment> = emptyList(),
) : CommitmentResolver {
    private val items = LinkedHashMap<Triple<String, String, String>, Commitment>()

    init {
        commitments.forEach { items[it.key] = it }
    }

    fun add(commitment: Commitment): Commitment {
        items[commitment.key] = commitment
        return commitment
    }

    override fun resolve(refs: List<CommitmentRef>): List<Commitment> =
        refs.mapNotNull { items[it.key] }
}

/**
 * Resolve every external reference in [local] and return its graph.
 *
 * The resolver may return fewer commitments than requested. The graph then
 * reports the unresolved references through `missingRefs`.
 */
fun resolveCommitmentGraph(
    local: CommitmentLedger,
    resolver: CommitmentResolver,
): CommitmentGraph {
    val refs = local.all()
        .flatMap { it.externalDependsOn }
        .distinct()
    return CommitmentGraph(local, resolver.resolve(refs))
}

/** Async variant of [resolveCommitmentGraph]. */
suspend fun resolveCommitmentGraphAsync(
    local: CommitmentLedger,
    resolver: AsyncCommitmentResolver,
): CommitmentGraph {
    val refs = local.all()
        .flatMap { it.externalDependsOn }
        .distinct()
    return CommitmentGraph(local, resolver.resolve(refs))
}
