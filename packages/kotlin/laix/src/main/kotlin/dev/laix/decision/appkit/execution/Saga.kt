package dev.laix.decision.appkit.execution

/** One forward action and its optional compensation. */
data class SagaStep(
    val name: String,
    val forward: () -> Map<String, Any?>,
    val compensate: (() -> Map<String, Any?>)? = null,
)

/** The outcome of one execution saga. */
data class SagaResult(
    val completed: List<String>,
    val compensated: List<String>,
    val error: String? = null,
)

/** Run steps in order and compensate the completed ones on failure. */
class Saga {
    fun run(steps: List<SagaStep>): SagaResult {
        val completed = mutableListOf<SagaStep>()
        try {
            for (step in steps) {
                step.forward()
                completed += step
            }
        } catch (exception: Exception) {
            val compensated = mutableListOf<String>()
            for (step in completed.reversed()) {
                val compensate = step.compensate ?: continue
                try {
                    compensate()
                    compensated += step.name
                } catch (_: Exception) {
                    // compensation is best effort
                }
            }
            return SagaResult(
                completed = completed.map { it.name },
                compensated = compensated,
                error = "${exception::class.simpleName}: ${exception.message}",
            )
        }
        return SagaResult(completed = completed.map { it.name }, compensated = emptyList())
    }
}
