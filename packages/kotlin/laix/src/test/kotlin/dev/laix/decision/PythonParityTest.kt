package dev.laix.decision

import dev.laix.decision.appkit.DecisionClient
import dev.laix.decision.appkit.audit.createRecord
import dev.laix.decision.appkit.audit.verify
import dev.laix.decision.appkit.streaming.StreamSession
import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.Goal
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.learning.model.ModelLearner
import dev.laix.decision.planners.explain.counterfactualAttribution
import dev.laix.decision.planners.utility.RiskAttitude
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.policies.packs.Rule
import dev.laix.decision.policies.packs.RulePolicy
import dev.laix.decision.support.iso
import dev.laix.decision.support.isoFull
import dev.laix.decision.support.policyTruthy
import dev.laix.decision.support.pythonEquals
import dev.laix.decision.support.pythonFloatRepr
import dev.laix.decision.support.pythonIn
import dev.laix.decision.support.pythonJsonString
import dev.laix.decision.support.round
import dev.laix.decision.support.round6
import dev.laix.decision.support.truthy
import java.time.OffsetDateTime
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Guards the places where Kotlin must behave like the Python reference. */
class PythonParityTest {
    @Test
    fun `round uses the exact binary double like Python`() {
        assertEquals(2.67, round(2.675, 2))
        assertEquals(1.0, round(1.005, 2))
        assertEquals(0.0, round(0.5, 0))
        assertEquals(2.0, round(1.5, 0))
        assertEquals(2.0, round(2.5, 0))
        // Python keeps the negative sign on a rounded-to-zero value.
        assertTrue(1.0 / round(-0.0000001, 6) < 0)
    }

    @Test
    fun `truthiness distinguishes bool from policy tokens`() {
        assertTrue(truthy("false"))
        assertTrue(truthy("0"))
        assertTrue(!truthy(""))
        assertTrue(truthy(1))
        assertTrue(!truthy(0))
        assertTrue(policyTruthy("true"))
        assertTrue(!policyTruthy("false"))
        assertTrue(!policyTruthy("anything else"))
    }

    @Test
    fun `python equality and membership coerce numbers`() {
        assertTrue(pythonEquals(500L, 500.0))
        assertTrue(pythonEquals(1, true))
        assertTrue(!pythonEquals("1", 1))
        assertTrue(pythonIn("abc", "b"))
        assertTrue(pythonIn(mapOf("a" to 1), "a"))
        assertTrue(pythonIn(listOf(1, 2), 2.0))
        assertTrue(!pythonIn("abc", "z"))
    }

    @Test
    fun `float repr follows Python formatting`() {
        assertEquals("0.1", pythonFloatRepr(0.1))
        assertEquals("0.8", pythonFloatRepr(0.8))
        assertEquals("1000000000000000.0", pythonFloatRepr(1e15))
        assertEquals("1e+16", pythonFloatRepr(1e16))
        assertEquals("1e-07", pythonFloatRepr(1e-7))
        assertEquals("-0.0", pythonFloatRepr(-0.0))
    }

    @Test
    fun `json strings escape non ascii like Python ensure_ascii`() {
        assertEquals("caf\\u00e9", pythonJsonString("café").trim('"'))
        assertEquals("\"a\\\"b\"", pythonJsonString("a\"b"))
        assertEquals("\"a\\\\b\"", pythonJsonString("a\\b"))
    }

    @Test
    fun `timestamps use python isoformat shapes`() {
        val microseconds = OffsetDateTime.parse("2026-11-01T10:00:00.123456Z")
        assertEquals("2026-11-01T10:00:00+00:00", iso(microseconds))
        assertEquals("2026-11-01T10:00:00.123456+00:00", isoFull(microseconds))
        val offset = OffsetDateTime.parse("2026-11-01T12:00:00+02:00")
        assertEquals("2026-11-01T10:00:00+00:00", iso(offset))
        // Python's isoformat keeps the moment's own offset.
        assertEquals("2026-11-01T12:00:00+02:00", isoFull(offset))
        assertEquals(java.time.ZoneOffset.UTC, dev.laix.decision.support.parseIso(offset.toString())!!.offset)
        assertEquals(
            java.time.ZoneOffset.ofHours(2),
            dev.laix.decision.support.parseIsoLocal(offset.toString())!!.offset,
        )
    }

    @Test
    fun `decision confidence is normalised on construct and copy`() {
        val decision = Decision(verb = Verb.ACT, confidence = 2.0, reasonCode = "r", rationale = "why")
        assertEquals(1.0, decision.confidence)
        assertEquals(0.0, decision.copy(confidence = -3.0).confidence)
        assertEquals(decision, decision.copy())
    }

    @Test
    fun `decision basis renders an intent like Python repr`() {
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.5,
            reasonCode = "r",
            rationale = "why",
            intent = Intent("act", mapOf("arm" to "a1")),
        )
        val note = decision.basis().first { it["kind"] == "intent" }["note"]
        assertEquals("{'arm': 'a1'}", note)
    }

    @Test
    fun `record payloads clamp their scores`() {
        assertEquals(1.0, Belief(id = "b", proposition = "p", confidence = 4.0).confidence)
        assertEquals(0.0, Goal(id = "g", statement = "s", priority = -1.0).priority)
        assertEquals(1.0, Observation("o", "at", "src", "kind", confidence = 3.0).confidence)
        val option = ActionOption("a", Verb.ACT, "act", expectedBenefit = 5.0, risk = 5.0)
        assertEquals(1.0, option.expectedBenefit)
        assertEquals(1.0, option.risk)
        val approved = ActionOption("a2", Verb.ACT, "act", destructive = true)
        assertTrue(approved.requiresApproval)
    }

    @Test
    fun `belief codecs coerce numbers and keep the band`() {
        val belief = Belief.fromMap(
            mapOf(
                "id" to "b",
                "proposition" to "p",
                "confidence" to "0.4",
                "updated_at" to "2026-11-01T10:00:00+00:00",
            ),
        )
        assertEquals(0.4, belief.confidence)
        assertEquals("low", belief.toMap()["band"])
        assertEquals(0.4, Belief.fromMap(belief.toMap()).confidence)
    }

    @Test
    fun `stream restore keeps the newest buffered decisions`() {
        val session = StreamSession({ emptyList() }, capacity = 2)
        fun decision(id: String) = Decision(
            verb = Verb.WAIT,
            confidence = 0.5,
            reasonCode = "r",
            rationale = "w",
            decisionId = id,
        )
        session.restore(
            mapOf(
                "stream_id" to "s-1",
                "pending" to listOf(
                    decision("d1").toMap(),
                    decision("d2").toMap(),
                    decision("d3").toMap(),
                ),
            ),
        )
        assertEquals(listOf("d2", "d3"), session.drain().map { it.decisionId })
    }

    @Test
    fun `decision record hashes non ascii payloads like Python`() {
        val record = createRecord(
            title = "Café",
            decision = "naïve",
            evidence = listOf(
                EvidenceRef(id = "e1", kind = "doc", source = "src", quote = "résumé", confidence = 0.9),
            ),
            confidence = 0.8,
            requiresApproval = true,
            metadata = mapOf("note" to "ação"),
            recordId = "dr-test",
            now = "2026-11-01T10:00:00+00:00",
        )
        assertEquals(
            "sha256:2a8e36dec31c1f96c1f54caf4b073e3152dc1ff31e743b5a72ba5af91fe25271",
            record.hash,
        )
        assertTrue(verify(record))
    }

    @Test
    fun `record id falls back when empty`() {
        val record = createRecord(
            title = "Pay",
            decision = "Pay the invoice",
            evidence = listOf(EvidenceRef(id = "e1")),
            recordId = "",
            now = "2026-11-01T10:00:00+00:00",
        )
        assertTrue(record.id.startsWith("dr-"))
        assertEquals(15, record.id.length)
    }

    @Test
    fun `rules compare numbers across Kotlin types`() {
        val policy = RulePolicy(
            listOf(Rule(condition = mapOf("score" to 500), verb = Verb.ACT, reasonCode = "hit")),
        )
        val request = DecisionRequest(
            subject = "s",
            at = iso(),
            attributes = mapOf("score" to 500.0),
        )
        assertEquals("hit", policy.decide(request).single().reasonCode)
    }

    @Test
    fun `rules support python membership over strings`() {
        val policy = RulePolicy(
            listOf(
                Rule(
                    condition = mapOf("state" to mapOf("in" to "abc")),
                    verb = Verb.ACT,
                    reasonCode = "hit",
                ),
            ),
        )
        val request = DecisionRequest(subject = "s", at = iso(), attributes = mapOf("state" to "b"))
        assertEquals("hit", policy.decide(request).single().reasonCode)
    }

    @Test
    fun `utility overrides need a hard limit`() {
        val model = UtilityModel(maxRisk = 0.5, riskAttitude = RiskAttitude.NEUTRAL)
        val problem = PlannerInput(
            subject = "s",
            at = iso(),
            attributes = mapOf("risk_attitude" to "seeking"),
        )
        val resolved = utilityModelFor(problem, model)
        assertEquals(RiskAttitude.NEUTRAL, resolved.riskAttitude)
        assertEquals(0.5, resolved.maxRisk)

        val withLimit = utilityModelFor(
            PlannerInput(
                subject = "s",
                at = iso(),
                attributes = mapOf("risk_attitude" to "seeking", "max_risk" to "0.9"),
            ),
            model,
        )
        assertEquals(RiskAttitude.SEEKING, withLimit.riskAttitude)
        assertEquals(0.9, withLimit.maxRisk)
    }

    @Test
    fun `status reports a policy version or none`() {
        val versioned = DecisionClient(policy = RulePolicy(emptyList()))
        assertEquals("rules.v1", versioned.status()["policyVersion"])

        val unversioned = DecisionClient(
            policy = object : DecisionPolicy {
                override val name: String = "custom.v1"
                override fun decide(request: DecisionRequest): List<Decision> = emptyList()
            },
        )
        assertNull(unversioned.status()["policyVersion"])

        val builtin = DecisionClient()
        assertEquals("0.8.0", builtin.status()["policyVersion"])
    }

    @Test
    fun `model learner ignores empty fallbacks`() {
        val learner = ModelLearner()
        learner.observe("start", "go", "end", 1.0)
        val model = learner.toMdpModel(states = emptyList(), actions = emptyList(), start = "")
        assertEquals(listOf("end", "start"), model.states)
        // Python: `start or known_states[0]`, so an empty start falls back.
        assertEquals("end", model.start)
    }

    @Test
    fun `counterfactual resulting total uses the unrounded delta`() {
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.5,
            reasonCode = "r",
            rationale = "why",
            actionId = "chosen",
            score = 0.5,
            attributes = mapOf("utility" to 0.5),
            alternatives = listOf(
                mapOf("action_id" to "other", "total" to 0.1234565, "utility" to 0.1),
            ),
        )
        val row = counterfactualAttribution(decision).minimal!!
        val rawDelta = 0.5 - 0.1234565 + 1e-6
        assertEquals(round6(rawDelta), row.delta)
        assertEquals(round6(0.1234565 + rawDelta), row.resultingTotal)
    }

    @Test
    fun `counterfactual search rejects an invalid grid`() {
        assertFailsWith<IllegalArgumentException> {
            dev.laix.decision.planners.explain.counterfactualSearch(
                { "a" },
                listOf(
                    dev.laix.decision.planners.explain.CounterfactualVariable(
                        name = "x",
                        value = 5.0,
                        lower = 0.0,
                        upper = 1.0,
                    ),
                ),
            )
        }
    }
}
