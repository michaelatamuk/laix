package dev.laix.decision.planners.fleet

import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.round6
import java.time.Duration
import java.time.OffsetDateTime

/**
 * One pending decision competing for human attention.
 *
 * Ranks each candidate by a Whittle-style index:
 * `expected gain * urgency - waiting cost) / review cost`.
 */
data class AttentionCandidate(
    val id: String,
    val risk: Double = 0.0,
    val value: Double = 0.0,
    val commitment: Boolean = false,
    val informationValue: Double = 0.0,
    val waitingCost: Double = 0.0,
    val reviewCost: Double = 1.0,
    val changeProbability: Double = 0.5,
    val deadline: String? = null,
    val params: Map<String, Any?> = emptyMap(),
)

/** The score and allocation for one candidate. */
data class AttentionScheduleRow(
    val candidateId: String,
    val index: Double,
    val expectedGain: Double,
    val urgency: Double,
    val reviewCost: Double,
    val selected: Boolean,
    val reason: String,
)

/** The ranked schedule and the budget it used. */
data class AttentionSchedule(
    val now: String,
    val budget: Double,
    val spent: Double,
    val rows: List<AttentionScheduleRow>,
    val selected: List<AttentionScheduleRow>,
    val deferred: List<AttentionScheduleRow>,
)

/** Rank pending decisions with an attention-aware index policy. */
class AttentionScheduler(
    val riskWeight: Double = 1.0,
    val commitmentWeight: Double = 0.5,
    val informationWeight: Double = 0.5,
    urgencyHorizonSeconds: Double = 3600.0,
) {
    val name: String = "aads.v1"
    val urgencyHorizonSeconds: Double = maxOf(1.0, urgencyHorizonSeconds)

    fun schedule(
        candidates: List<AttentionCandidate>,
        now: Any? = null,
        budget: Double = 1.0,
    ): AttentionSchedule {
        val current = asDateTime(now)
        val limit = maxOf(0.0, budget)
        val ordered = candidates.map { candidate ->
            val reviewCost = maxOf(1e-9, candidate.reviewCost)
            val stakes = maxOf(0.0, candidate.value) +
                riskWeight * maxOf(0.0, candidate.risk) +
                commitmentWeight * (if (candidate.commitment) 1.0 else 0.0) +
                informationWeight * maxOf(0.0, candidate.informationValue)
            val expectedGain = maxOf(0.0, candidate.changeProbability) * stakes
            val urgency = urgency(candidate.deadline, current)
            val index = (expectedGain * urgency - maxOf(0.0, candidate.waitingCost)) / reviewCost
            Scored(candidate, index, expectedGain, urgency)
        }.sortedWith(compareBy({ -it.index }, { it.candidate.id }))

        var spent = 0.0
        val rows = ordered.map { scored ->
            val reviewCost = maxOf(1e-9, scored.candidate.reviewCost)
            val selected = spent + reviewCost <= limit + 1e-9
            if (selected) spent += reviewCost
            AttentionScheduleRow(
                candidateId = scored.candidate.id,
                index = round6(scored.index),
                expectedGain = round6(scored.expectedGain),
                urgency = round6(scored.urgency),
                reviewCost = round6(reviewCost),
                selected = selected,
                reason = if (selected) "within attention budget" else "attention budget exhausted",
            )
        }

        return AttentionSchedule(
            now = current.toString(),
            budget = round6(limit),
            spent = round6(spent),
            rows = rows,
            selected = rows.filter { it.selected },
            deferred = rows.filter { !it.selected },
        )
    }

    private fun urgency(deadline: String?, now: OffsetDateTime): Double {
        if (deadline.isNullOrEmpty()) return 1.0
        val due = asDateTime(deadline)
        val seconds = Duration.between(now, due).toMillis() / 1000.0
        if (seconds <= 0) return 1.0 + urgencyHorizonSeconds
        return 1.0 + urgencyHorizonSeconds / maxOf(1.0, seconds)
    }

    private data class Scored(
        val candidate: AttentionCandidate,
        val index: Double,
        val expectedGain: Double,
        val urgency: Double,
    )
}

private fun asDateTime(value: Any?): OffsetDateTime =
    when (value) {
        null -> dev.laix.decision.support.utcNow()
        is OffsetDateTime -> value
        is String -> parseIso(value) ?: dev.laix.decision.support.utcNow()
        else -> parseIso(value.toString()) ?: dev.laix.decision.support.utcNow()
    }
