package dev.laix.decision.planners.explain

import dev.laix.decision.support.round

/** One bounded input to the decision function. */
data class CounterfactualVariable(
    val name: String,
    val value: Double,
    val lower: Double,
    val upper: Double,
    val step: Double = 0.1,
    val weight: Double = 1.0,
)

/** One changed variable. */
data class CounterfactualChange(
    val name: String,
    val old: Double,
    val new: Double,
    val delta: Double,
)

/** The chosen action and the smallest searched counterfactual. */
data class CounterfactualSearchResult(
    val chosenId: String,
    val counterfactualId: String?,
    val changes: List<CounterfactualChange>,
    val distance: Double,
    val evaluations: Int,
)

private fun round9(value: Double): Double = round(value, 9)

private fun grid(variable: CounterfactualVariable): List<Double> {
    require(variable.step > 0) { "step must be positive" }
    require(variable.lower <= variable.upper) { "lower must not exceed upper" }
    require(variable.value in variable.lower..variable.upper) {
        "value must be inside [lower, upper]"
    }
    val count = round((variable.upper - variable.lower) / variable.step, 0).toInt()
    val values = sortedSetOf<Double>()
    for (index in 0..count) {
        values += round9(variable.lower + index * variable.step)
    }
    values += round9(variable.value)
    return values.toList()
}

/**
 * Find the smallest weighted L1 change that flips the decision.
 *
 * The search is deterministic and exact over the generated grid when the budget
 * is not reached.
 */
fun counterfactualSearch(
    decide: (Map<String, Double>) -> String,
    variables: List<CounterfactualVariable>,
    maxChanges: Int = 2,
    maxEvaluations: Int = 20000,
): CounterfactualSearchResult {
    require(maxChanges >= 1) { "max_changes must be at least one" }
    require(maxEvaluations >= 1) { "max_evaluations must be at least one" }
    val base = variables.associate { it.name to it.value }
    val chosen = decide(base)
    val grids = variables.associate { it.name to grid(it) }

    data class Candidate(
        val distance: Double,
        val names: List<String>,
        val values: List<Double>,
    )

    val candidates = mutableListOf<Candidate>()
    val limit = minOf(maxChanges, variables.size)
    for (size in 1..limit) {
        for (group in combinations(variables, size)) {
            val names = group.map { it.name }
            for (values in product(names.map { grids.getValue(it) })) {
                val changes = names.indices
                    .filter { kotlin.math.abs(values[it] - base.getValue(names[it])) > 1e-12 }
                if (changes.isEmpty()) continue
                var distance = 0.0
                for (variable in variables) {
                    val newValue = if (variable.name in names) {
                        values[names.indexOf(variable.name)]
                    } else {
                        variable.value
                    }
                    distance += variable.weight * kotlin.math.abs(newValue - variable.value)
                }
                candidates += Candidate(round9(distance), names, values)
            }
        }
    }
    candidates.sortWith(
        Comparator { left, right ->
            val byDistance = left.distance.compareTo(right.distance)
            if (byDistance != 0) return@Comparator byDistance
            val byNames = compareNames(left.names, right.names)
            if (byNames != 0) return@Comparator byNames
            compareValues(left.values, right.values)
        },
    )

    var evaluations = 0
    for (candidate in candidates) {
        if (evaluations >= maxEvaluations) break
        val probe = LinkedHashMap(base)
        for (index in candidate.names.indices) {
            probe[candidate.names[index]] = candidate.values[index]
        }
        val result = decide(probe)
        evaluations++
        if (result == chosen) continue
        val changes = candidate.names.indices
            .filter { kotlin.math.abs(candidate.values[it] - base.getValue(candidate.names[it])) > 1e-12 }
            .map { index ->
                val name = candidate.names[index]
                val value = candidate.values[index]
                CounterfactualChange(
                    name = name,
                    old = round9(base.getValue(name)),
                    new = round9(value),
                    delta = round9(value - base.getValue(name)),
                )
            }
        return CounterfactualSearchResult(
            chosenId = chosen,
            counterfactualId = result,
            changes = changes,
            distance = round9(candidate.distance),
            evaluations = evaluations,
        )
    }
    return CounterfactualSearchResult(
        chosenId = chosen,
        counterfactualId = null,
        changes = emptyList(),
        distance = 0.0,
        evaluations = evaluations,
    )
}

private fun compareNames(left: List<String>, right: List<String>): Int {
    for (index in 0 until minOf(left.size, right.size)) {
        val compared = left[index].compareTo(right[index])
        if (compared != 0) return compared
    }
    return left.size.compareTo(right.size)
}

private fun compareValues(left: List<Double>, right: List<Double>): Int {
    for (index in 0 until minOf(left.size, right.size)) {
        val compared = left[index].compareTo(right[index])
        if (compared != 0) return compared
    }
    return left.size.compareTo(right.size)
}

private fun <T> combinations(items: List<T>, size: Int): List<List<T>> {    val result = mutableListOf<List<T>>()
    fun walk(start: Int, current: MutableList<T>) {
        if (current.size == size) {
            result += current.toList()
            return
        }
        for (index in start until items.size) {
            current += items[index]
            walk(index + 1, current)
            current.removeAt(current.lastIndex)
        }
    }
    walk(0, mutableListOf())
    return result
}

private fun <T> product(lists: List<List<T>>): List<List<T>> {
    var result = listOf(emptyList<T>())
    for (list in lists) {
        result = result.flatMap { prefix -> list.map { prefix + it } }
    }
    return result
}
