package dev.laix.decision.learning.calibration

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round

/** Predicted and observed rates for one confidence interval. */
data class CalibrationBin(
    val lower: Double,
    val upper: Double,
    val predicted: Double,
    val observed: Double,
    val count: Int,
)

/** One prediction and whether it turned out to be correct. */
@ConsistentCopyVisibility
data class CalibrationSample private constructor(
    val confidence: Double,
    val correct: Boolean,
    val policy: String,
) {
    companion object {
        operator fun invoke(
            confidence: Double,
            correct: Boolean,
            policy: String = "",
        ): CalibrationSample = create(clamp(confidence), correct, policy)

        private fun create(
            confidence: Double,
            correct: Boolean,
            policy: String,
        ): CalibrationSample = CalibrationSample(confidence, correct, policy)
    }
}

/** One decision and whether it turned out to be correct. */
@ConsistentCopyVisibility
data class DecisionCalibrationSample private constructor(
    val confidence: Double,
    val correct: Boolean,
    val verb: String,
    val actionId: String,
    val policy: String,
) {
    companion object {
        operator fun invoke(
            confidence: Double,
            correct: Boolean,
            verb: String = "",
            actionId: String = "",
            policy: String = "",
        ): DecisionCalibrationSample =
            create(clamp(confidence), correct, verb, actionId, policy)

        private fun create(
            confidence: Double,
            correct: Boolean,
            verb: String,
            actionId: String,
            policy: String,
        ): DecisionCalibrationSample =
            DecisionCalibrationSample(confidence, correct, verb, actionId, policy)
    }
}

/** A reliability summary for one policy or one sample set. */
data class CalibrationReport(
    val samples: Int,
    val accuracy: Double,
    val expected: Double,
    val error: Double,
    val bins: List<CalibrationBin>,
    val policy: String = "",
    val smoothing: Double = 0.0,
) {
    /** Map one confidence value onto the observed rate. */
    fun adjust(confidence: Double): Double {
        for (item in bins) {
            if (item.count > 0 && confidence >= item.lower && confidence < item.upper) {
                return clamp(item.observed)
            }
            if (item.count > 0 && confidence == 1.0 && item.upper == 1.0) {
                return clamp(item.observed)
            }
        }
        return clamp(confidence - (expected - accuracy))
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "samples" to samples,
            "accuracy" to accuracy,
            "expected" to expected,
            "error" to error,
            "policy" to policy,
            "smoothing" to smoothing,
            "bins" to bins.map {
                linkedMapOf(
                    "lower" to it.lower,
                    "upper" to it.upper,
                    "predicted" to it.predicted,
                    "observed" to it.observed,
                    "count" to it.count,
                )
            },
        )
}

/** A reliability summary for decisions, with per-verb and per-action accuracy. */
data class DecisionCalibrationReport(
    val samples: Int,
    val accuracy: Double,
    val expected: Double,
    val error: Double,
    val bins: List<CalibrationBin>,
    val verbAccuracy: Map<String, Double>,
    val actionAccuracy: Map<String, Double>,
    val policy: String = "",
    val smoothing: Double = 0.0,
) {
    /** Map one confidence value onto the observed decision rate. */
    fun adjust(confidence: Double): Double {
        for (item in bins) {
            if (item.count > 0 && confidence >= item.lower && confidence < item.upper) {
                return clamp(item.observed)
            }
            if (item.count > 0 && confidence == 1.0 && item.upper == 1.0) {
                return clamp(item.observed)
            }
        }
        return clamp(confidence - (expected - accuracy))
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "samples" to samples,
            "accuracy" to accuracy,
            "expected" to expected,
            "error" to error,
            "policy" to policy,
            "smoothing" to smoothing,
            "bins" to bins.map {
                linkedMapOf(
                    "lower" to it.lower,
                    "upper" to it.upper,
                    "predicted" to it.predicted,
                    "observed" to it.observed,
                    "count" to it.count,
                )
            },
            "verb_accuracy" to verbAccuracy,
            "action_accuracy" to actionAccuracy,
        )

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): DecisionCalibrationReport =
            DecisionCalibrationReport(
                samples = (payload["samples"] as? Number)?.toInt() ?: 0,
                accuracy = (payload["accuracy"] as? Number)?.toDouble() ?: 0.0,
                expected = (payload["expected"] as? Number)?.toDouble() ?: 0.0,
                error = (payload["error"] as? Number)?.toDouble() ?: 0.0,
                bins = (payload["bins"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.let {
                        CalibrationBin(
                            lower = (it["lower"] as? Number)?.toDouble() ?: 0.0,
                            upper = (it["upper"] as? Number)?.toDouble() ?: 0.0,
                            predicted = (it["predicted"] as? Number)?.toDouble() ?: 0.0,
                            observed = (it["observed"] as? Number)?.toDouble() ?: 0.0,
                            count = (it["count"] as? Number)?.toInt() ?: 0,
                        )
                    }
                } ?: emptyList(),
                verbAccuracy = (payload["verb_accuracy"] as? Map<*, *>)?.entries?.associate {
                    it.key.toString() to ((it.value as? Number)?.toDouble() ?: 0.0)
                } ?: emptyMap(),
                actionAccuracy = (payload["action_accuracy"] as? Map<*, *>)?.entries?.associate {
                    it.key.toString() to ((it.value as? Number)?.toDouble() ?: 0.0)
                } ?: emptyMap(),
                policy = payload["policy"]?.toString() ?: "",
                smoothing = (payload["smoothing"] as? Number)?.toDouble() ?: 0.0,
            )
    }
}

private fun binRows(
    buckets: List<List<Pair<Double, Boolean>>>,
    bins: Int,
    smoothing: Double,
): List<CalibrationBin> {
    val rows = mutableListOf<CalibrationBin>()
    for ((index, bucket) in buckets.withIndex()) {
        if (bucket.isEmpty()) continue
        val correct = bucket.count { it.second }
        val observed = (correct + smoothing) / (bucket.size + 2.0 * smoothing)
        rows += CalibrationBin(
            lower = round(index.toDouble() / bins, 6),
            upper = round((index + 1).toDouble() / bins, 6),
            predicted = round(bucket.sumOf { it.first } / bucket.size, 6),
            observed = round(observed, 6),
            count = bucket.size,
        )
    }
    return rows
}

/**
 * Compare stated confidence with observed accuracy.
 *
 * [smoothing] applies Laplace smoothing to each bin's observed rate.
 */
fun calibrationReport(
    samples: List<CalibrationSample>,
    bins: Int = 10,
    policy: String = "",
    smoothing: Double = 0.0,
): CalibrationReport {
    require(bins >= 1) { "bins must be at least one" }
    require(smoothing >= 0) { "smoothing must not be negative" }
    if (samples.isEmpty()) {
        return CalibrationReport(
            samples = 0,
            accuracy = 0.0,
            expected = 0.0,
            error = 0.0,
            bins = emptyList(),
            policy = policy,
            smoothing = smoothing,
        )
    }
    val buckets = List(bins) { mutableListOf<Pair<Double, Boolean>>() }
    for (item in samples) {
        val index = minOf((item.confidence * bins).toInt(), bins - 1)
        buckets[index] += item.confidence to item.correct
    }
    val rows = binRows(buckets, bins, smoothing)
    val accuracy = samples.count { it.correct }.toDouble() / samples.size
    val expected = samples.sumOf { it.confidence } / samples.size
    return CalibrationReport(
        samples = samples.size,
        accuracy = round(accuracy, 6),
        expected = round(expected, 6),
        error = round(kotlin.math.abs(expected - accuracy), 6),
        bins = rows,
        policy = policy,
        smoothing = smoothing,
    )
}

/** Build one report per policy name. */
fun calibrationByPolicy(
    samples: List<CalibrationSample>,
    bins: Int = 10,
    smoothing: Double = 0.0,
): Map<String, CalibrationReport> {
    val grouped = samples.groupBy { it.policy }.toSortedMap()
    return grouped.mapValues { (policy, items) ->
        calibrationReport(items, bins, policy, smoothing)
    }
}

/**
 * Turn measured outcomes into calibration samples.
 *
 * A decision counts as correct when its outcome label is `helped`.
 */
fun samplesFromOutcomes(
    outcomes: List<Outcome>,
    confidences: Map<String, Double>,
    policies: Map<String, String>? = null,
): List<CalibrationSample> =
    outcomes.mapNotNull { outcome ->
        confidences[outcome.decisionId]?.let { confidence ->
            CalibrationSample(
                confidence = confidence,
                correct = outcome.label == "helped",
                policy = policies?.get(outcome.decisionId) ?: "",
            )
        }
    }

/** Compare stated confidence with observed decision accuracy. */
fun decisionCalibrationReport(
    samples: List<DecisionCalibrationSample>,
    bins: Int = 10,
    policy: String = "",
    smoothing: Double = 0.0,
): DecisionCalibrationReport {
    require(bins >= 1) { "bins must be at least one" }
    require(smoothing >= 0) { "smoothing must not be negative" }
    if (samples.isEmpty()) {
        return DecisionCalibrationReport(
            samples = 0,
            accuracy = 0.0,
            expected = 0.0,
            error = 0.0,
            bins = emptyList(),
            verbAccuracy = emptyMap(),
            actionAccuracy = emptyMap(),
            policy = policy,
            smoothing = smoothing,
        )
    }
    val buckets = List(bins) { mutableListOf<Pair<Double, Boolean>>() }
    for (item in samples) {
        val index = minOf((item.confidence * bins).toInt(), bins - 1)
        buckets[index] += item.confidence to item.correct
    }
    val rows = binRows(buckets, bins, smoothing)
    val accuracy = samples.count { it.correct }.toDouble() / samples.size
    val expected = samples.sumOf { it.confidence } / samples.size
    return DecisionCalibrationReport(
        samples = samples.size,
        accuracy = round(accuracy, 6),
        expected = round(expected, 6),
        error = round(kotlin.math.abs(expected - accuracy), 6),
        bins = rows,
        verbAccuracy = accuracyBy(samples) { it.verb },
        actionAccuracy = accuracyBy(samples) { it.actionId },
        policy = policy,
        smoothing = smoothing,
    )
}

private fun accuracyBy(
    samples: List<DecisionCalibrationSample>,
    key: (DecisionCalibrationSample) -> String,
): Map<String, Double> {
    val buckets = LinkedHashMap<String, MutableList<Boolean>>()
    for (item in samples) {
        val value = key(item)
        if (value.isEmpty()) continue
        buckets.getOrPut(value) { mutableListOf() } += item.correct
    }
    return buckets.toSortedMap().mapValues { (_, flags) ->
        round(flags.count { it }.toDouble() / flags.size, 6)
    }
}

/** Turn measured outcomes into decision-level calibration samples. */
fun decisionSamplesFromOutcomes(
    decisions: List<Decision>,
    outcomes: List<Outcome>,
    policies: Map<String, String>? = null,
): List<DecisionCalibrationSample> {
    val byId = decisions.associateBy { it.decisionId }
    return outcomes.mapNotNull { outcome ->
        byId[outcome.decisionId]?.let { decision ->
            DecisionCalibrationSample(
                confidence = decision.confidence,
                correct = outcome.label == "helped",
                verb = decision.verb.value,
                actionId = decision.actionId ?: "",
                policy = policies?.get(decision.decisionId) ?: "",
            )
        }
    }
}

/** Wrap any policy and calibrate every decision it returns. */
class CalibratedPolicy(
    val policy: DecisionPolicy,
    val report: DecisionCalibrationReport,
    name: String? = null,
) : DecisionPolicy {
    override val name: String = name ?: "${policy.name.ifEmpty { "policy" }}.calibrated"
    val version: String = this.name

    override fun decide(request: DecisionRequest): List<Decision> =
        policy.decide(request).map { calibrateDecision(it, report) }
}

/** Return a copy of [decision] with calibrated confidence and metadata. */
fun calibrateDecision(
    decision: Decision,
    report: DecisionCalibrationReport,
    source: String = "decision-calibration",
): Decision {
    if (report.samples == 0) return decision
    val adjusted = report.adjust(decision.confidence)
    val attributes = LinkedHashMap(decision.attributes)
    attributes["calibration"] = linkedMapOf(
        "before" to decision.confidence,
        "after" to adjusted,
        "samples" to report.samples,
        "accuracy" to report.accuracy,
    )
    return decision.copy(
        confidence = adjusted,
        calibrated = true,
        confidenceSource = source,
        attributes = attributes,
    )
}
