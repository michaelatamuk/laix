package dev.laix.examples.decision.learning

import dev.laix.decision.learning.bandit.Arm
import dev.laix.decision.learning.bandit.UCBBandit
import dev.laix.decision.learning.calibration.CalibrationSample
import dev.laix.decision.learning.calibration.calibrationReport
import dev.laix.decision.learning.causal.CausalLedger
import dev.laix.decision.learning.model.ModelLearner
import dev.laix.examples.AT

/** Compare predicted confidence with observed accuracy. */
fun calibration(): String {
    val samples = listOf(
        CalibrationSample(confidence = 0.9, correct = true),
        CalibrationSample(confidence = 0.9, correct = true),
        CalibrationSample(confidence = 0.6, correct = false),
        CalibrationSample(confidence = 0.6, correct = true),
        CalibrationSample(confidence = 0.3, correct = false),
    )
    val report = calibrationReport(samples, bins = 5)
    return "samples=${report.samples} accuracy=${report.accuracy} " +
        "expected=${report.expected} error=${report.error}"
}

/** Explore two arms, update one, then choose again. */
fun banditLearning(): String {
    val bandit = UCBBandit(listOf(Arm("arm-a"), Arm("arm-b")))
    val first = bandit.choose()?.id
    bandit.update("arm-a", 1.0)
    bandit.update("arm-b", 0.0)
    val second = bandit.choose()?.id
    return "first=$first second=$second meanA=${bandit.mean("arm-a")} " +
        "meanB=${bandit.mean("arm-b")}"
}

/** Learn transition probabilities and rewards from observed steps. */
fun modelLearning(): String {
    val learner = ModelLearner()
    learner.observe("start", "go", "middle", 1.0)
    learner.observe("start", "go", "middle", 1.0)
    learner.observe("start", "wait", "start", 0.0)
    learner.observe("middle", "go", "end", 1.0)
    val distribution = learner.transitionProbabilities("start", "go")
    val model = learner.toMdpModel()
    return "p(middle)=${distribution["middle"]} reward=${learner.expectedReward("start", "go")} " +
        "states=${model.states}"
}

/** Estimate a treatment effect from two arms in an outcome log. */
fun causalAttribution(): String {
    val ledger = CausalLedger()
    ledger.add("d1", arm = "reminder", outcome = 1.0)
    ledger.add("d2", arm = "reminder", outcome = 1.0)
    ledger.add("d3", arm = "reminder", outcome = 0.0)
    ledger.add("d4", arm = "control", outcome = 0.0)
    ledger.add("d5", arm = "control", outcome = 1.0)
    ledger.add("d6", arm = "control", outcome = 0.0)
    val effect = ledger.effect("reminder", "control")
    return "estimate=${effect.estimate} method=${effect.method} " +
        "treated=${effect.treated} control=${effect.controlSize}"
}

/** A measured outcome is also a bandit reward. */
fun outcomeReward(): String {
    val ledger = dev.laix.decision.outcomes.OutcomeLedger()
    val outcome = ledger.record("DEC-1", metric = "precision", before = 0.5, after = 0.9, attributed = true)
    val reward = dev.laix.decision.learning.bandit.rewardForLabel(outcome.label)
    return "label=${outcome.label} reward=$reward measuredAt=${outcome.measuredAt.isNotEmpty()}"
}
