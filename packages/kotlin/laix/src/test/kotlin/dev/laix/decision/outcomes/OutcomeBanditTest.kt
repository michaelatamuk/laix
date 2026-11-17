package dev.laix.decision.outcomes

import dev.laix.decision.learning.bandit.Arm
import dev.laix.decision.learning.bandit.UCBBandit
import dev.laix.decision.learning.bandit.rewardForLabel
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

class OutcomeBanditTest {
    @Test
    fun `labels follow the measured direction`() {
        val ledger = OutcomeLedger()

        val helped = ledger.record(
            "DEC-1",
            metric = "precision",
            before = 0.5,
            after = 0.8,
            attributed = true,
        )
        assertEquals("helped", helped.label)

        val hurt = ledger.record(
            "DEC-2",
            metric = "time_to_assessment",
            before = 10.0,
            after = 4.0,
            direction = "lower-better",
        )
        assertEquals("helped", hurt.label)

        val neutral = ledger.record(
            "DEC-3",
            metric = "precision",
            before = 0.5,
            after = 0.5,
        )
        assertEquals("neutral", neutral.label)

        assertFailsWith<IllegalArgumentException> {
            ledger.record("DEC-4", metric = "m", before = 0.0, after = 0.0, direction = "sideways")
        }
    }

    @Test
    fun `summary separates attribution coverage`() {
        val ledger = OutcomeLedger()
        ledger.record("DEC-1", metric = "precision", before = 0.0, after = 1.0, attributed = true)
        ledger.record("DEC-2", metric = "precision", before = 1.0, after = 0.0, attributed = true)
        ledger.record("DEC-3", metric = "precision", before = 0.0, after = 1.0)

        val summary = ledger.summary()

        assertEquals(3, summary["measured"])
        assertEquals(2, summary["attributed"])
        assertEquals(0.667, summary["attributionCoverage"])
        assertEquals(1, summary["helped"])
        assertEquals(1, summary["hurt"])
        assertEquals(0.0, summary["meanGain"])
        assertEquals(0.5, summary["precision"])
    }

    @Test
    fun `outcomes round-trip through JSON`() {
        val ledger = OutcomeLedger()
        ledger.record(
            "DEC-1",
            metric = "precision",
            before = 0.2,
            after = 0.6,
            attributed = true,
            evidence = mapOf("sample" to 10L),
            note = "measured",
        )

        val restored = OutcomeLedger.fromJson(ledger.toJson())
        assertEquals(ledger.toMap()["records"], restored.toMap()["records"])
        assertEquals(ledger.summary(), restored.summary())
    }

    @Test
    fun `rewards map labels and skip unknown`() {
        assertEquals(1.0, rewardForLabel("helped"))
        assertEquals(0.5, rewardForLabel("neutral"))
        assertEquals(0.0, rewardForLabel("hurt"))
        assertNull(rewardForLabel("unknown"))
        assertNull(rewardForLabel(null))
    }

    @Test
    fun `the bandit explores an unpulled arm first`() {
        val bandit = UCBBandit(listOf(Arm("a"), Arm("b")))

        assertEquals(Double.POSITIVE_INFINITY, bandit.score("a"))
    }

    @Test
    fun `the bandit learns from outcomes`() {
        val bandit = UCBBandit(listOf(Arm("a"), Arm("b", priorMean = 0.4)))
        val ledger = OutcomeLedger()
        val helped = ledger.record(
            "DEC-1",
            metric = "m",
            before = 0.0,
            after = 1.0,
            label = "helped",
            attributed = true,
        )

        assertEquals(1, bandit.learn(listOf(helped), { "a" }))
        assertEquals(1, bandit.pulls("a"))
        assertTrue(bandit.mean("a") > 0.5)
    }

    @Test
    fun `the bandit respects risk and budget`() {
        val bandit = UCBBandit(
            listOf(
                Arm("cheap", cost = 1.0, risk = 0.1),
                Arm("risky", cost = 1.0, risk = 0.9),
                Arm("expensive", cost = 10.0, risk = 0.1),
            ),
        )

        assertEquals("cheap", bandit.choose(maxRisk = 0.5, budget = 5.0)?.id)
        assertNull(bandit.choose(maxRisk = 0.0, budget = 0.0))
        assertEquals("cheap", bandit.choose(exclude = listOf("risky"))?.id)
    }

    @Test
    fun `arms clamp their priors`() {
        assertEquals(1.0, Arm("a", priorMean = 2.0).priorMean)
        assertEquals(0.0, Arm("a", priorMean = -1.0).priorMean)
        assertEquals(0.0, Arm("a", priorWeight = -1.0).priorWeight)
        assertFailsWith<IllegalArgumentException> { UCBBandit().add(Arm("  ")) }
    }

    @Test
    fun `bandit policy accepts arm objects and maps`() {
        val policy = dev.laix.decision.policies.packs.BanditPolicy()
        val request = dev.laix.decision.contracts.DecisionRequest(
            subject = "s",
            at = "2026-11-01T10:00:00+00:00",
            attributes = mapOf(
                "arms" to listOf(
                    Arm("existing", priorMean = 0.1),
                    mapOf("id" to "mapped", "prior_mean" to 0.9),
                ),
            ),
        )
        val decision = policy.decide(request).single()

        assertEquals(
            listOf("existing", "mapped"),
            policy.bandit.arms().map { it.id },
        )
        assertEquals(dev.laix.decision.contracts.Verb.ACT, decision.verb)
        assertEquals("existing", decision.actionId)
    }

    @Test
    fun `bandit maps carry pulls and means`() {
        val bandit = UCBBandit(listOf(Arm("a")))
        bandit.update("a", 1.0)

        val payload = bandit.toMap()
        assertEquals(1.4, payload["exploration"])
        @Suppress("UNCHECKED_CAST")
        val arms = payload["arms"] as List<Map<String, Any?>>
        assertEquals(1, arms.first()["pulls"])
        assertEquals(0.75, arms.first()["mean"])
    }
}
