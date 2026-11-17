package dev.laix.decision.planners

import dev.laix.decision.planners.fleet.AttentionCandidate
import dev.laix.decision.planners.fleet.AttentionScheduler
import dev.laix.decision.planners.fleet.WhittleCandidate
import dev.laix.decision.planners.fleet.WhittleScheduler
import dev.laix.decision.planners.fleet.WhittleTransition
import dev.laix.decision.planners.fleet.whittleIndex
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class FleetSchedulersTest {
    @Test
    fun `the scheduler prefers the urgent high-risk review`() {
        val schedule = AttentionScheduler().schedule(
            listOf(
                AttentionCandidate(
                    id = "urgent",
                    risk = 0.9,
                    commitment = true,
                    reviewCost = 1.0,
                    deadline = "2026-11-01T10:01:00+00:00",
                ),
                AttentionCandidate(
                    id = "routine",
                    risk = 0.1,
                    reviewCost = 1.0,
                    deadline = "2026-11-01T11:00:00+00:00",
                ),
            ),
            now = "2026-11-01T10:00:00+00:00",
            budget = 1.0,
        )

        assertEquals("urgent", schedule.selected.first().candidateId)
        assertEquals(1.0, schedule.spent)
        assertEquals("routine", schedule.deferred.first().candidateId)
    }

    @Test
    fun `the scheduler respects the budget and explains`() {
        val schedule = AttentionScheduler().schedule(
            listOf(
                AttentionCandidate(id = "a", risk = 0.8, reviewCost = 0.75),
                AttentionCandidate(id = "b", risk = 0.6, reviewCost = 0.75),
            ),
            now = "2026-11-01T10:00:00+00:00",
            budget = 1.0,
        )

        assertEquals(listOf("a"), schedule.selected.map { it.candidateId })
        assertEquals("b", schedule.deferred.first().candidateId)
        assertEquals("attention budget exhausted", schedule.deferred.first().reason)
    }

    @Test
    fun `an empty schedule is valid`() {
        val schedule = AttentionScheduler().schedule(
            emptyList(),
            now = "2026-11-01T10:00:00+00:00",
        )

        assertEquals(emptyList(), schedule.selected)
        assertEquals(emptyList(), schedule.deferred)
        assertEquals(0.0, schedule.spent)
    }

    private fun candidate(id: String, reward: Double) = WhittleCandidate(
        id = id,
        states = listOf("bad", "good"),
        start = "bad",
        activeTransitions = listOf(
            WhittleTransition("bad", "good"),
            WhittleTransition("good", "good"),
        ),
        passiveTransitions = listOf(
            WhittleTransition("bad", "bad"),
            WhittleTransition("good", "good"),
        ),
        activeReward = mapOf("bad" to reward, "good" to 0.2),
        passiveReward = mapOf("bad" to 0.0, "good" to 0.0),
        activeCost = 0.1,
        reviewCost = 1.0,
        discount = 0.9,
    )

    @Test
    fun `higher active reward has a higher index`() {
        val high = whittleIndex(candidate("high", 1.0))
        val low = whittleIndex(candidate("low", 0.1))

        assertTrue(high > low)
        assertTrue(high > 0)
    }

    @Test
    fun `the whittle scheduler allocates by index`() {
        val schedule = WhittleScheduler().schedule(
            listOf(candidate("low", 0.1), candidate("high", 1.0)),
            budget = 1.0,
        )

        assertEquals("high", schedule.selected.first().candidateId)
        assertEquals("low", schedule.deferred.first().candidateId)
        assertEquals(1.0, schedule.spent)
    }

    @Test
    fun `candidates are validated`() {
        assertFailsWith<IllegalArgumentException> {
            whittleIndex(candidate("bad", 1.0).copy(states = emptyList()))
        }
        assertFailsWith<IllegalArgumentException> {
            whittleIndex(
                candidate("bad", 1.0).copy(
                    activeTransitions = listOf(WhittleTransition("bad", "missing")),
                ),
            )
        }
    }
}
