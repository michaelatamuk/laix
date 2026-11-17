package dev.laix.examples.appkit.connect

import dev.laix.decision.appkit.delivery.NullDelivery
import dev.laix.decision.appkit.platform.ApprovalDecision
import dev.laix.decision.appkit.platform.ApprovalRequest
import dev.laix.decision.appkit.platform.InMemoryPlatform
import dev.laix.decision.appkit.platform.SkillCall
import dev.laix.decision.appkit.state.ExperienceState
import dev.laix.decision.appkit.state.InMemoryStateStore
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.examples.AT

/** Persist experience state and load it back. */
fun stateStore(): String {
    val store = InMemoryStateStore()
    val state = ExperienceState(subject = "kitchen sink")
    state.setBelief(
        Belief(
            id = "leak",
            proposition = "the sink is leaking",
            confidence = 0.9,
            updatedAt = AT,
        ),
    )
    state.advance("understand")
    store.save("kitchen sink", state)

    val loaded = store.load("kitchen sink") ?: error("state was not saved")
    return "phase=${loaded.phase} beliefs=${loaded.beliefs.size} confidence=${loaded.confidence()}"
}

/** The platform seam: skills, approvals, state and events. */
fun platform(): String {
    val platform = InMemoryPlatform(
        approver = { request -> ApprovalDecision(approved = true, by = "lead", at = AT) },
    )
    platform.register("echo") { call -> call.args["text"] }
    val output = platform.runSkill(
        SkillCall(capability = "echo", args = mapOf("text" to "pay invoice 4832"), traceId = "TRC-1"),
    )
    val approval = platform.requestApproval(
        ApprovalRequest(decisionId = "DEC-1", actionName = "pay_bill", rationale = "due today"),
    )
    return "skill=$output approved=${approval.approved} by=${approval.by} " +
        "events=${platform.events("TRC-1").size}"
}

/** Delivery is a host port; the null port records what would have been sent. */
fun delivery(): String {
    val decision = Decision(
        verb = Verb.GUIDE,
        confidence = 0.8,
        reasonCode = "share",
        rationale = "share the update",
        decisionId = "DEC-1",
    )
    val port = NullDelivery()
    val receipt = port.deliver(decision, "The invoice is due today", channel = "email")
    return "status=${receipt.status} channel=${receipt.channel} receipts=${port.receipts.size}"
}
