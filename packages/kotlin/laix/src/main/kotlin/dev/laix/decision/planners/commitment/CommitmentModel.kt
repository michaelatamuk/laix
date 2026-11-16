package dev.laix.decision.planners.commitment

import dev.laix.decision.contracts.ActionOption

/** How much each commitment effect changes the utility score. */
data class CommitmentWeights(
    val keep: Double = 0.35,
    val violate: Double = 1.0,
    val create: Double = 0.10,
    val due: Double = 0.25,
    val blocked: Double = 0.50,
) {
    init {
        for ((name, value) in listOf(
            "keep" to keep,
            "violate" to violate,
            "create" to create,
            "due" to due,
            "blocked" to blocked,
        )) {
            require(value >= 0) { "commitment weight '$name' must not be negative" }
        }
    }
}

/** What one option does to the open commitments. */
@ConsistentCopyVisibility
data class CommitmentEffect private constructor(
    val fulfills: List<String>,
    val violates: List<String>,
    val creates: List<String>,
    val hard: Boolean,
) {
    companion object {
        operator fun invoke(
            fulfills: Any? = null,
            violates: Any? = null,
            creates: Any? = null,
            hard: Boolean = false,
        ): CommitmentEffect =
            CommitmentEffect(
                fulfills = commitmentIds(fulfills),
                violates = commitmentIds(violates),
                creates = commitmentIds(creates),
                hard = hard,
            )
    }
}

/** Normalise commitment identifiers. */
internal fun commitmentIds(value: Any?): List<String> =
    when (value) {
        null -> emptyList()
        is String -> listOf(value)
        is Map<*, *> -> listOf(value["id"]?.toString() ?: value.toString())
        is Iterable<*> -> value.map { item ->
            if (item is Map<*, *>) item["id"]?.toString() ?: item.toString() else item.toString()
        }
        else -> listOf(value.toString())
    }

/** The utility and commitment parts of one option's score. */
data class CommitmentScore(
    val utility: Double,
    val commitment: Double,
    val total: Double,
    val fulfilled: List<String> = emptyList(),
    val violated: List<String> = emptyList(),
    val created: List<String> = emptyList(),
    val dueFulfilled: List<String> = emptyList(),
    val dueViolated: List<String> = emptyList(),
    val blockedFulfilled: List<String> = emptyList(),
    val blocked: String? = null,
)

/**
 * Read an option's commitment effect from `params`.
 *
 * Supported shapes:
 *
 * ```
 * params = mapOf("commitments" to mapOf("fulfills" to listOf("c1"), "violates" to listOf("c2")))
 * params = mapOf("fulfills" to listOf("c1"), "creates" to listOf(mapOf("id" to "c3")))
 * ```
 */
fun commitmentEffect(option: ActionOption): CommitmentEffect {
    val params = option.params
    val raw = params["commitments"] ?: params["commitment"] ?: params
    val payload = raw as? Map<*, *> ?: return CommitmentEffect()

    fun pick(key: String): Any? {
        val value = payload[key]
        if (value == null && payload !== params) return params[key]
        return value
    }

    return CommitmentEffect(
        fulfills = pick("fulfills"),
        violates = pick("violates"),
        creates = pick("creates"),
        hard = pythonBool(pick("hard")),
    )
}

private fun pythonBool(value: Any?): Boolean =
    when (value) {
        null -> false
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        is String -> value.isNotEmpty()
        is Collection<*> -> value.isNotEmpty()
        is Map<*, *> -> value.isNotEmpty()
        else -> true
    }
