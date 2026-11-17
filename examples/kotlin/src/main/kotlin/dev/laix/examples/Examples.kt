package dev.laix.examples

import dev.laix.examples.appkit.build.*
import dev.laix.examples.appkit.connect.*
import dev.laix.examples.appkit.execute.*
import dev.laix.examples.appkit.run.*
import dev.laix.examples.decision.domain.*
import dev.laix.examples.decision.evaluation.*
import dev.laix.examples.decision.explain.*
import dev.laix.examples.decision.fleet.*
import dev.laix.examples.decision.learning.*
import dev.laix.examples.decision.perception.*
import dev.laix.examples.decision.sequence.*
import dev.laix.examples.decision.single.decide.*
import dev.laix.examples.decision.single.planners.*
import dev.laix.examples.decision.single.policies.*

/** Every example, in reading order. The order is the CLI listing order. */
val examples: List<Example> = listOf(
    // decision / single / decide
    Example(
        "decision/single/decide/action",
        "one action decision without the app kit",
    ) { actionDecide() },
    Example(
        "decision/single/decide/attention",
        "one signal-attention decision",
    ) { attentionDecide() },
    Example(
        "decision/single/decide/attention-below-floor",
        "a signal that stays silent",
    ) { attentionBelowFloor() },

    // decision / single / planners
    Example("decision/single/planners/utility", "score options and pick the highest expected utility") {
        utilityPlanner()
    },
    Example("decision/single/planners/commitment", "keep an open promise") { commitmentPlanner() },
    Example("decision/single/planners/execution", "prefer the reversible action when risk is unknown") {
        executionRiskPlanner()
    },
    Example("decision/single/planners/human-attention", "respect a nearly exhausted attention budget") {
        humanAttentionPlanner()
    },
    Example("decision/single/planners/live-composite", "utility, commitment, execution and attention together") {
        liveCompositePlanner()
    },
    Example("decision/single/planners/hard-constraint", "a hard latency limit removes an option") {
        hardConstraint()
    },
    Example("decision/single/planners/approval", "flag a payment that needs an approver") { approvalDecision() },
    Example("decision/single/planners/mdp", "walk a finite MDP toward the reward") { mdpPlanner() },
    Example("decision/single/planners/pomdp", "decide under uncertainty about the state") { pomdpPlanner() },
    Example("decision/single/planners/ca-vod", "price the value of deciding later") { cavodPlanner() },
    Example("decision/single/planners/portfolio", "route to the planner that fits the request") {
        portfolioPlanner()
    },
    Example("decision/single/planners/case-based", "reuse a past decision for a similar subject") {
        caseBasedPlanner()
    },
    Example("decision/single/planners/risk-bounded", "reject an option above the worst-case loss") {
        riskBoundedPlanner()
    },
    Example("decision/single/planners/conflict", "resolve two disagreeing goals") { conflictResolution() },

    // decision / single / policies
    Example("decision/single/policies/rules", "declarative rules over request attributes") { rulePolicy() },
    Example("decision/single/policies/safety", "the packaged safety policy") { safetyConstrainedPolicy() },
    Example("decision/single/policies/verification", "choose a check that closes the confidence gap") {
        verificationPolicy()
    },
    Example("decision/single/policies/preference", "ask the question with the highest information gain") {
        preferenceElicitation()
    },
    Example("decision/single/policies/active-perception", "admit the sensor inside the budget") {
        activePerception()
    },
    Example("decision/single/policies/replanning", "replan when the plan no longer clears the bar") {
        replanningPolicy()
    },
    Example("decision/single/policies/escalation", "escalate past the current owner") { escalationPolicy() },
    Example("decision/single/policies/negotiation", "counter inside the reservation and target") {
        negotiationPolicy()
    },
    Example("decision/single/policies/allocation", "allocate a fixed budget") { allocationPolicy() },
    Example("decision/single/policies/bandit", "learn which arm works") { banditPolicy() },
    Example("decision/single/policies/group", "share with a group and mask private fields") { groupPolicy() },
    Example("decision/single/policies/targeted", "route the decision to another recipient set") {
        targetedPolicy()
    },
    Example("decision/single/policies/shadow", "compare a primary and a shadow policy") { shadowPolicy() },

    // decision / sequence
    Example("decision/sequence/cabb", "plan two steps ahead with bounded search") { cabbPlan() },
    Example("decision/sequence/rollout", "roll out the same scenario one option at a time") { rolloutPlan() },
    Example("decision/sequence/replan", "replan after the first action was executed") { replan() },

    // decision / fleet
    Example("decision/fleet/attention-scheduler", "rank a fleet by expected gain per review minute") {
        attentionScheduler()
    },
    Example("decision/fleet/whittle", "rank the same fleet by its Whittle index") { whittleScheduler() },

    // decision / explain
    Example("decision/explain/attribution", "the smallest single-component change that flips a decision") {
        counterfactualAttribution()
    },
    Example("decision/explain/search", "search bounded inputs for a flip") { counterfactualSearchExample() },
    Example("decision/explain/decision-counterfactual", "solve a candidate problem and compare actions") {
        decisionCounterfactual()
    },

    // decision / domain
    Example("decision/domain/commitment-graph", "combine a local promise with another owner") {
        commitmentGraph()
    },
    Example("decision/domain/outcomes", "record what changed after a decision") { outcomeLedger() },
    Example("decision/domain/signal-outcomes", "score the attention policy on labelled signals") {
        signalAttentionOutcomes()
    },

    // decision / learning
    Example("decision/learning/calibration", "compare predicted confidence with accuracy") { calibration() },
    Example("decision/learning/bandit", "explore two arms, update one and choose again") { banditLearning() },
    Example("decision/learning/model", "learn transitions and rewards from observed steps") { modelLearning() },
    Example("decision/learning/causal", "estimate a treatment effect from two arms") { causalAttribution() },
    Example("decision/learning/outcome-reward", "turn a measured outcome into a bandit reward") {
        outcomeReward()
    },

    // decision / evaluation
    Example("decision/evaluation/cases", "replay labelled cases and report agreement") { evaluationCases() },
    Example("decision/evaluation/bench", "run the packaged decision-class bench") { decisionBench() },
    Example("decision/evaluation/simulation", "compare a planner with a do-nothing baseline") {
        plannerSimulation()
    },
    Example("decision/evaluation/live-bench", "run the live bench and print its metrics") { liveBench() },

    // decision / perception
    Example("decision/perception/resources", "admit the sensor calls that fit the budget") {
        resourceScheduler()
    },
    Example("decision/perception/live-context", "run detectors over an event") { liveContext() },

    // appkit / build
    Example("appkit/build/client", "the public client: one request in, one decision out") {
        decisionClient()
    },
    Example("appkit/build/policy-selection", "register a custom policy and switch to it") {
        policySelection()
    },
    Example("appkit/build/runtime", "state, trace and the action policy together") { decisionRuntime() },
    Example("appkit/build/runtime-execution", "execute through the bridge and keep receipts") {
        runtimeExecution()
    },
    Example("appkit/build/planner-policy", "put a planner behind the policy contract") { plannerAsPolicy() },
    Example("appkit/build/planner-input", "the planner input shape") { plannerInputShape() },
    Example("appkit/build/option-intent", "an option can carry the params the host executes") { optionIntent() },

    // appkit / run
    Example("appkit/run/stream-session", "admit events into one stream and drain decisions") {
        streamSession()
    },
    Example("appkit/run/checkpoint", "save a stream snapshot and resume it") { streamCheckpoint() },
    Example("appkit/run/feed", "feed a flow of requests") { streamFeed() },
    Example("appkit/run/windows", "aggregate events into tumbling windows") { tumblingWindow() },
    Example("appkit/run/ndjson", "read one request per JSON line") { ndjsonSource() },
    Example("appkit/run/timeline", "keep a decision timeline and find the current decision") {
        decisionTimeline()
    },

    // appkit / execute
    Example("appkit/execute/execution", "execute one action through a host handler") { execution() },
    Example("appkit/execute/idempotency", "the same key does not send twice") { idempotentExecution() },
    Example("appkit/execute/saga", "compensate a completed step when a later one fails") {
        executionSaga()
    },
    Example("appkit/execute/approval", "a destructive decision needs an approver") { approvalRequired() },
    Example("appkit/execute/record", "seal, approve, execute, undo and verify a record") {
        decisionRecord()
    },
    Example("appkit/execute/proposal", "the app-facing approval lifecycle") { proposal() },

    // appkit / connect
    Example("appkit/connect/state-store", "persist experience state and load it back") { stateStore() },
    Example("appkit/connect/platform", "skills, approvals, state and events") { platform() },
    Example("appkit/connect/delivery", "deliver through a host port") { delivery() },
)
