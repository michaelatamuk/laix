package dev.laix.decision.planners.history

import dev.laix.decision.support.round6

/** One record in the decision history. */
data class ContinuityRecord(
    val id: String,
    val kind: String,
    val status: String,
    val refs: List<String> = emptyList(),
    val conflicts: List<String> = emptyList(),
    val supports: List<String> = emptyList(),
    val cost: Double = 1.0,
    val payload: Map<String, Any?> = emptyMap(),
)

/** One conflict rule: (left kind, left status, right kind, right status). */
data class ConflictRule(
    val leftKind: String,
    val leftStatus: String,
    val rightKind: String,
    val rightStatus: String,
)

val DEFAULT_CONFLICT_RULES: List<ConflictRule> = listOf(
    ConflictRule("approval", "rejected", "receipt", "executed"),
    ConflictRule("commitment", "cancelled", "commitment", "done"),
    ConflictRule("decision", "superseded", "decision", "final"),
)

/** One planned revision. */
data class RepairAction(
    val recordId: String,
    val action: String,
    val fromStatus: String,
    val toStatus: String,
    val cost: Double,
    val reason: String,
)

/** The conflicts found and the repair they imply. */
data class RepairPlan(
    val conflicts: List<Pair<String, String>>,
    val actions: List<RepairAction>,
    val totalCost: Double,
    val consistent: Boolean,
    val method: String = "greedy",
)

private fun sharedRefs(left: ContinuityRecord, right: ContinuityRecord): Boolean =
    left.refs.toSet().intersect(right.refs.toSet()).isNotEmpty()

private fun matches(
    left: ContinuityRecord,
    right: ContinuityRecord,
    rule: ConflictRule,
): Boolean =
    left.kind == rule.leftKind &&
        left.status == rule.leftStatus &&
        right.kind == rule.rightKind &&
        right.status == rule.rightStatus

private fun conflictPairs(
    records: List<ContinuityRecord>,
    rules: List<ConflictRule>,
): List<Pair<ContinuityRecord, ContinuityRecord>> {
    val byId = records.associateBy { it.id }
    val pairs = LinkedHashMap<Pair<String, String>, Pair<ContinuityRecord, ContinuityRecord>>()

    for (record in records) {
        for (otherId in record.conflicts) {
            val other = byId[otherId] ?: continue
            if (other.id == record.id) continue
            val key = listOf(record.id, other.id).sorted().let { it[0] to it[1] }
            pairs[key] = record to other
        }
    }

    for (index in records.indices) {
        val left = records[index]
        for (rightIndex in index + 1 until records.size) {
            val right = records[rightIndex]
            if (!sharedRefs(left, right)) continue
            if (rules.any { matches(left, right, it) || matches(right, left, it) }) {
                val key = listOf(left.id, right.id).sorted().let { it[0] to it[1] }
                pairs.putIfAbsent(key, left to right)
            }
        }
    }

    return pairs.values.toList()
}

/** Exact minimum-weight vertex cover by branch and bound. */
private fun minimumVertexCover(
    pairs: List<Pair<ContinuityRecord, ContinuityRecord>>,
): Set<String> {
    if (pairs.isEmpty()) return emptySet()
    val records = mutableMapOf<String, ContinuityRecord>()
    for ((left, right) in pairs) {
        records[left.id] = left
        records[right.id] = right
    }
    val edges = pairs.map { setOf(it.first.id, it.second.id) }
    var bestCost = Double.POSITIVE_INFINITY
    var bestSet: Set<String> = emptySet()

    fun search(remaining: List<Set<String>>, chosen: Set<String>, cost: Double) {
        if (remaining.isEmpty()) {
            if (cost < bestCost) {
                bestCost = cost
                bestSet = chosen.toSet()
            }
            return
        }
        if (cost >= bestCost) return
        val edge = remaining.maxByOrNull { item ->
            item.minOf { node -> records.getValue(node).cost }
        } ?: return
        val order = edge.sortedWith(compareBy({ records.getValue(it).cost }, { it }))
        for (node in order) {
            search(
                remaining.filter { node !in it },
                chosen + node,
                cost + maxOf(0.0, records.getValue(node).cost),
            )
        }
    }

    search(edges, emptySet(), 0.0)
    return bestSet
}

/**
 * Find conflicts and repair them.
 *
 * The default is the greedy minimum-cost repair. Pass `exact = true` to solve
 * the minimum-weight vertex cover by branch and bound.
 */
fun repairContinuity(
    records: List<ContinuityRecord>,
    rules: List<ConflictRule> = DEFAULT_CONFLICT_RULES,
    exact: Boolean = false,
): RepairPlan {
    val conflicts = conflictPairs(records, rules)
    val active = conflicts.filter {
        it.first.status != "superseded" && it.second.status != "superseded"
    }
    val actions = mutableListOf<RepairAction>()

    if (exact) {
        val selected = minimumVertexCover(active)
        for (recordId in selected.sorted()) {
            val record = records.first { it.id == recordId }
            actions += RepairAction(
                recordId = record.id,
                action = "supersede",
                fromStatus = record.status,
                toStatus = "superseded",
                cost = round6(maxOf(0.0, record.cost)),
                reason = "minimum-weight vertex cover",
            )
        }
    } else {
        for ((left, right) in active) {
            val (target, other) = when {
                left.cost < right.cost -> left to right
                right.cost < left.cost -> right to left
                left.id > right.id -> left to right
                else -> right to left
            }
            actions += RepairAction(
                recordId = target.id,
                action = "supersede",
                fromStatus = target.status,
                toStatus = "superseded",
                cost = round6(maxOf(0.0, target.cost)),
                reason = "conflicts with ${other.id}",
            )
        }
    }

    val conflictIds = conflicts.map { (left, right) ->
        listOf(left.id, right.id).sorted().let { it[0] to it[1] }
    }
    return RepairPlan(
        conflicts = conflictIds,
        actions = actions,
        totalCost = round6(actions.sumOf { it.cost }),
        consistent = active.isEmpty(),
        method = if (exact) "exact" else "greedy",
    )
}
