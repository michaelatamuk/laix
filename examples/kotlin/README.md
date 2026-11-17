# Kotlin examples

Sixty-four runnable examples, one Gradle project. Each example prints one line, and every example is
executed by `ExamplesTest` and by CI.

## Run

From the repository root:

```powershell
# list the examples
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="--list"

# run everything
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="--all"

# run a path substring
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="decision/single/planners"

# run the example suite as a test
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin test
```

The project uses the local package as a composite build, so it always runs against the working tree:

```kotlin
// settings.gradle.kts
includeBuild("../../packages/kotlin/laix")
```

## Layout

| Folder | Examples |
|---|---|
| `decision/single/decide` | action decision, signal attention, a silent signal |
| `decision/single/planners` | utility, commitment, execution, human attention, live composite, hard constraints, approval, MDP, POMDP, CA-VOD, portfolio, case-based, risk bound, conflict |
| `decision/single/policies` | rules, safety, verification, preference, active perception, replanning, escalation, negotiation, allocation, bandit, group, targeted, shadow |
| `decision/sequence` | CABB, rollout, replan |
| `decision/fleet` | attention scheduler, Whittle index |
| `decision/explain` | attribution, search, decision counterfactual |
| `decision/domain` | commitment graph, outcome ledger, signal outcomes |
| `decision/learning` | calibration, bandit, model learning, causal attribution, outcome reward |
| `decision/evaluation` | cases, decision bench, planner simulation, live bench |
| `decision/perception` | resource admission, live context |
| `appkit/build` | client, policy selection, runtime, runtime execution, planner policy, option intent |
| `appkit/run` | stream session, checkpoint, feed, windows, NDJSON, timeline |
| `appkit/execute` | execution, idempotency, saga, approval, record, proposal |
| `appkit/connect` | state store, platform, delivery |

## Examples

```text
decision/single/decide/action                  one action decision without the app kit
decision/single/decide/attention               one signal-attention decision
decision/single/decide/attention-below-floor   a signal that stays silent
decision/single/planners/utility               score options and pick the highest expected utility
decision/single/planners/commitment            keep an open promise
decision/single/planners/execution             prefer the reversible action when risk is unknown
decision/single/planners/human-attention       respect a nearly exhausted attention budget
decision/single/planners/live-composite        utility, commitment, execution and attention together
decision/single/planners/hard-constraint       a hard latency limit removes an option
decision/single/planners/approval              flag a payment that needs an approver
decision/single/planners/mdp                   walk a finite MDP toward the reward
decision/single/planners/pomdp                 decide under uncertainty about the state
decision/single/planners/ca-vod                price the value of deciding later
decision/single/planners/portfolio             route to the planner that fits the request
decision/single/planners/case-based            reuse a past decision for a similar subject
decision/single/planners/risk-bounded          reject an option above the worst-case loss
decision/single/planners/conflict              resolve two disagreeing goals
decision/single/policies/rules                 declarative rules over request attributes
decision/single/policies/safety                the packaged safety policy
decision/single/policies/verification          choose a check that closes the confidence gap
decision/single/policies/preference            ask the question with the highest information gain
decision/single/policies/active-perception     admit the sensor inside the budget
decision/single/policies/replanning            replan when the plan no longer clears the bar
decision/single/policies/escalation            escalate past the current owner
decision/single/policies/negotiation           counter inside the reservation and target
decision/single/policies/allocation            allocate a fixed budget
decision/single/policies/bandit                learn which arm works
decision/single/policies/group                 share with a group and mask private fields
decision/single/policies/targeted              route the decision to another recipient set
decision/single/policies/shadow                compare a primary and a shadow policy
decision/sequence/cabb                         plan two steps ahead with bounded search
decision/sequence/rollout                      roll out the scenario one option at a time
decision/sequence/replan                       replan after the first action was executed
decision/fleet/attention-scheduler             rank a fleet by expected gain per review minute
decision/fleet/whittle                         rank the same fleet by its Whittle index
decision/explain/attribution                   the smallest change that flips a decision
decision/explain/search                        search bounded inputs for a flip
decision/explain/decision-counterfactual       solve a candidate problem and compare actions
decision/domain/commitment-graph               combine a local promise with another owner
decision/domain/outcomes                       record what changed after a decision
decision/domain/signal-outcomes                score the attention policy on labelled signals
decision/learning/calibration                  compare predicted confidence with accuracy
decision/learning/bandit                       explore two arms, update one and choose again
decision/learning/model                        learn transitions and rewards from observed steps
decision/learning/causal                       estimate a treatment effect from two arms
decision/learning/outcome-reward               turn a measured outcome into a bandit reward
decision/evaluation/cases                      replay labelled cases and report agreement
decision/evaluation/bench                      run the packaged decision-class bench
decision/evaluation/simulation                 compare a planner with a do-nothing baseline
decision/evaluation/live-bench                 run the live bench and print its metrics
decision/perception/resources                  admit the sensor calls that fit the budget
decision/perception/live-context               run detectors over an event
appkit/build/client                            the public client
appkit/build/policy-selection                  register a custom policy and switch to it
appkit/build/runtime                           state, trace and the action policy together
appkit/build/runtime-execution                 execute through the bridge and keep receipts
appkit/build/planner-policy                    put a planner behind the policy contract
appkit/build/planner-input                     the planner input shape
appkit/build/option-intent                     an option can carry the params the host executes
appkit/run/stream-session                      admit events into one stream and drain decisions
appkit/run/checkpoint                          save a stream snapshot and resume it
appkit/run/feed                                feed a flow of requests
appkit/run/windows                             aggregate events into tumbling windows
appkit/run/ndjson                              read one request per JSON line
appkit/run/timeline                            keep a decision timeline
appkit/execute/execution                       execute one action through a host handler
appkit/execute/idempotency                     the same key does not send twice
appkit/execute/saga                            compensate a completed step when a later one fails
appkit/execute/approval                        a destructive decision needs an approver
appkit/execute/record                          seal, approve, execute, undo and verify a record
appkit/execute/proposal                        the app-facing approval lifecycle
appkit/connect/state-store                     persist experience state and load it back
appkit/connect/platform                        skills, approvals, state and events
appkit/connect/delivery                        deliver through a host port
```

## Output

The suite is deterministic. A few lines:

```text
act policy_rule option-close-valve conf=0.95
guide worth_surfacing - conf=0.9
act expected_utility option-close-valve score=0.936875
act live_decision safe commitment=0.35
act goal_conflict_resolved resolve
verify/verify_outcome/api
actions=[send, verify] score=1.4 optimal=true nodes=5
minimal counterfactual: alternative=other component=utility delta=0.300001
commitments=2 missing=0 trusted=true
samples=5 accuracy=0.6 expected=0.66 error=0.06
2/2 agreement=1.0
status=undone verified=true audit=4
status=executed actor=agent detail={sent=true, channel=email}
first=executed second=duplicate original=true
```

The output shape mirrors the Python and TypeScript examples where the same story exists. Random ids
are never printed, so the output is stable across runs.

## See also

- [Kotlin guide](../../docs/01-start/02-first-steps/03-kotlin.md)
- [Package README](../../packages/kotlin/laix/README.md)
- [Examples index](../README.md)
