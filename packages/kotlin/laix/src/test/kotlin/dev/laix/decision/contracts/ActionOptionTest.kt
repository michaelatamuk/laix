package dev.laix.decision.contracts

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ActionOptionTest {
    @Test
    fun `out-of-range scores are clamped`() {
        val option = ActionOption(
            id = "a-1",
            verb = Verb.ACT,
            name = "clamped",
            expectedBenefit = 1.7,
            risk = -0.4,
            interruptCost = 2.0,
        )

        assertEquals(1.0, option.expectedBenefit)
        assertEquals(0.0, option.risk)
        assertEquals(1.0, option.interruptCost)
        assertEquals(0.85, option.utility)
    }

    @Test
    fun `destructive options always require approval`() {
        val option = ActionOption(
            id = "a-2",
            verb = Verb.ACT,
            name = "delete",
            destructive = true,
        )

        assertTrue(option.requiresApproval)
    }
}
