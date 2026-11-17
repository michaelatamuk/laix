package dev.laix.decision.learning

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Verb
import dev.laix.decision.learning.calibration.CalibratedPolicy
import dev.laix.decision.learning.calibration.CalibrationSample
import dev.laix.decision.learning.calibration.DecisionCalibrationReport
import dev.laix.decision.learning.calibration.DecisionCalibrationSample
import dev.laix.decision.learning.calibration.calibrateDecision
import dev.laix.decision.learning.calibration.calibrationByPolicy
import dev.laix.decision.learning.calibration.calibrationReport
import dev.laix.decision.learning.calibration.decisionCalibrationReport
import dev.laix.decision.learning.calibration.decisionSamplesFromOutcomes
import dev.laix.decision.learning.calibration.samplesFromOutcomes
import dev.laix.decision.outcomes.Outcome
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class CalibrationTest {
    private fun samples(policy: String = "") =
        (0 until 10).map {
            CalibrationSample(confidence = 0.9, correct = it < 5, policy = policy)
        }

    @Test
    fun `the report compares expected and observed`() {
        val report = calibrationReport(samples())

        assertEquals(10, report.samples)
        assertEquals(0.9, report.expected)
        assertEquals(0.5, report.accuracy)
        assertEquals(0.4, report.error)
        assertEquals(10, report.bins.first().count)
        assertEquals(0.5, report.bins.first().observed)
    }

    @Test
    fun `adjust uses the observed rate`() {
        val report = calibrationReport(samples())

        assertEquals(0.5, report.adjust(0.9))
    }

    @Test
    fun `smoothing regularises small bins`() {
        val report = calibrationReport(
            listOf(CalibrationSample(confidence = 0.9, correct = true)),
            smoothing = 1.0,
        )

        assertEquals(1.0, report.smoothing)
        assertEquals(0.666667, report.bins.first().observed)
        assertEquals(0.666667, report.adjust(0.9))
    }

    @Test
    fun `reports are grouped by policy`() {
        val reports = calibrationByPolicy(samples("rules") + samples("bandit"))

        assertEquals(listOf("bandit", "rules"), reports.keys.toList())
        assertEquals(10, reports.getValue("rules").samples)
    }

    @Test
    fun `outcomes become samples`() {
        val outcomes = listOf(
            Outcome(
                id = "o1",
                decisionId = "d1",
                metric = "precision",
                before = 0.5,
                after = 0.8,
                delta = 0.3,
                label = "helped",
            ),
            Outcome(
                id = "o2",
                decisionId = "d2",
                metric = "precision",
                before = 0.5,
                after = 0.4,
                delta = -0.1,
                label = "hurt",
            ),
        )

        val rows = samplesFromOutcomes(
            outcomes,
            mapOf("d1" to 0.8, "d2" to 0.7),
            mapOf("d1" to "rules", "d2" to "rules"),
        )

        assertEquals(listOf(true, false), rows.map { it.correct })
        assertEquals(setOf("rules"), rows.map { it.policy }.toSet())
    }

    @Test
    fun `decision calibration bins and adjusts confidence`() {
        val rows = buildList {
            repeat(8) { add(DecisionCalibrationSample(0.9, true, verb = "act", actionId = "send")) }
            repeat(2) { add(DecisionCalibrationSample(0.9, false, verb = "act", actionId = "send")) }
            repeat(2) { add(DecisionCalibrationSample(0.2, true, verb = "wait")) }
            repeat(8) { add(DecisionCalibrationSample(0.2, false, verb = "wait")) }
        }
        val report = decisionCalibrationReport(rows)

        assertEquals(20, report.samples)
        assertEquals(0.5, report.accuracy)
        assertEquals(0.55, report.expected)
        assertEquals(0.05, report.error)
        assertEquals(0.8, report.adjust(0.9))
        assertEquals(0.2, report.adjust(0.2))
        assertEquals(0.8, report.verbAccuracy["act"])
        assertEquals(0.8, report.actionAccuracy["send"])
    }

    @Test
    fun `decision reports round-trip`() {
        val report = decisionCalibrationReport(
            (0 until 10).map {
                DecisionCalibrationSample(0.9, it < 5)
            },
        )
        val restored = DecisionCalibrationReport.fromMap(report.toMap())

        assertEquals(report.samples, restored.samples)
        assertEquals(report.accuracy, restored.accuracy)
        assertEquals(report.adjust(0.9), restored.adjust(0.9))
    }

    @Test
    fun `an empty report is neutral`() {
        val report = decisionCalibrationReport(emptyList())

        assertEquals(0, report.samples)
        assertEquals(emptyList(), report.bins)
        assertEquals(0.7, report.adjust(0.7))
        assertEquals(emptyMap<String, Double>(), report.toMap()["verb_accuracy"])
    }

    @Test
    fun `calibrating a decision preserves it`() {
        val report = decisionCalibrationReport(
            (0 until 10).map { DecisionCalibrationSample(0.9, it < 5) },
        )
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.9,
            reasonCode = "expected_utility",
            rationale = "the valve is the best option",
            decisionId = "d1",
            actionId = "valve",
        )

        val calibrated = calibrateDecision(decision, report)

        assertEquals(0.5, calibrated.confidence)
        assertEquals(true, calibrated.calibrated)
        assertEquals("decision-calibration", calibrated.confidenceSource)
        assertEquals(Verb.ACT, calibrated.verb)
        assertEquals("valve", calibrated.actionId)
        @Suppress("UNCHECKED_CAST")
        val metadata = calibrated.attributes["calibration"] as Map<String, Any?>
        assertEquals(0.9, metadata["before"])
        assertEquals(0.5, metadata["after"])
    }

    @Test
    fun `a calibrated policy wraps any policy`() {
        val fake = object : DecisionPolicy {
            override val name: String = "fake"

            override fun decide(request: DecisionRequest): List<Decision> =
                listOf(
                    Decision(
                        verb = Verb.ACT,
                        confidence = 0.9,
                        reasonCode = "fake",
                        rationale = "a fake decision",
                        decisionId = "d1",
                    ),
                )
        }
        val report = decisionCalibrationReport(
            (0 until 10).map { DecisionCalibrationSample(0.9, it < 5) },
        )
        val policy = CalibratedPolicy(fake, report)

        val decisions = policy.decide(
            DecisionRequest(subject = "a", at = "2026-11-01T10:00:00+00:00"),
        )

        assertEquals("fake.calibrated", policy.name)
        assertEquals(0.5, decisions.first().confidence)
        assertEquals(true, decisions.first().calibrated)
    }

    @Test
    fun `samples from outcomes use the decision shape`() {
        val decision = Decision(
            verb = Verb.ACT,
            confidence = 0.8,
            reasonCode = "r",
            rationale = "why",
            decisionId = "d1",
            actionId = "a1",
        )
        val outcome = Outcome(
            id = "o1",
            decisionId = "d1",
            metric = "saved",
            before = 0.0,
            after = 1.0,
            delta = 1.0,
            label = "helped",
        )

        val rows = decisionSamplesFromOutcomes(listOf(decision), listOf(outcome))

        assertEquals(1, rows.size)
        assertEquals(true, rows.first().correct)
        assertEquals("act", rows.first().verb)
        assertEquals("a1", rows.first().actionId)
    }

    @Test
    fun `invalid arguments are rejected`() {
        assertFailsWith<IllegalArgumentException> { decisionCalibrationReport(emptyList(), bins = 0) }
        assertFailsWith<IllegalArgumentException> { decisionCalibrationReport(emptyList(), smoothing = -1.0) }
        assertTrue(CalibrationSample(2.0, true).confidence == 1.0)
    }
}
