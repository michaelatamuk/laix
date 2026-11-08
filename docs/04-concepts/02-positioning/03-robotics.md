# LAIX for robotics

LAIX can sit in the **task-decision layer** of a robot. It is not a robot control framework, a
motion planner or a safety controller.

The useful split is:

| Layer | Owns | LAIX |
|---|---|---|
| **Task decision** | What should the robot do next? Act, ask, wait, verify or escalate. | **Yes** |
| **Reflex and control** | Perception, SLAM, motion planning, trajectory control, motor control, e-stop and safety functions. | **No** |

LAIX decides. The robot's safety layer disposes.

## Where it fits well

LAIX is a good fit for discrete, task-level decisions such as:

- continue, ask for help, wait, abort or escalate;
- approve or reject a physical action;
- keep a promise such as "deliver this before the shift ends";
- recover from a failed step;
- hand over to a person when confidence or attention is low;
- carry task state across a sequence of decisions;
- produce an audit trail for a regulated deployment.

| Robot type | Fit |
|---|---|
| Warehouse AMR and service robot | **Good** for task decisions and supervision. |
| Inspection and agricultural robot | **Good** for mission decisions and escalation. |
| Lab automation | **Good** for task-level approvals and continuity. |
| Humanoid or mobile manipulator | **Good above** the safety and motion layer. |
| Industrial arm | **Only outside** the safety function. |
| Surgical robot | **No** in the control or safety path. |
| Drone or autonomous vehicle | **No** in the real-time safety loop; possible for fleet or operations decisions. |

## Where it does not fit

Do not put LAIX in the hard real-time or safety-critical loop.

- It has no hard real-time guarantees, no WCET and no RTOS integration.
- It is a Python and TypeScript library; the host owns process priority, scheduling and watchdogs.
- It does not provide functional safety, redundancy, e-stop logic or certified safety functions.
- It does not provide perception, SLAM, sensor fusion, motion planning or trajectory control.
- Its planners are decision planners, not motion planners.
- A Python policy must not be the thing that decides whether an arm stops before touching a person.

`Constraint` values and hard gates are decision inputs. They are not a substitute for a certified
safety controller.

## Integration shape

```text
mission planner / operator
          |
          v
LAIX task decision  -->  Decision: act / ask / wait / verify / escalate
          |
          v
safety supervisor    -->  hard veto, e-stop, speed limits, zones
          |
          v
ROS 2 / motion / control / actuators
```

A clean loop:

1. The robot builds a `DecisionRequest` from the current task state.
2. LAIX returns a `Decision`.
3. The robot maps the chosen action to a ROS 2 action, skill or behavior.
4. The safety supervisor checks the action independently.
5. The robot executes, records a receipt and measures the outcome.
6. The next request carries commitments, attention budget, approvals, receipts and outcomes.

The host supplies the robot state, the available skills and the execution handlers. LAIX supplies the
decision, its reason, the approval flag, the execution risk and the trail.

## What is missing

A real robotics deployment would need host-side work:

- a ROS 2 adapter for actions, services and topics;
- a safety-supervisor contract that sits between LAIX and the actuators;
- a deterministic timing budget, deadlines and watchdogs;
- a robot-state adapter for battery, pose, zone, payload, task phase and human proximity;
- a simulation adapter for Gazebo, Isaac Sim or MuJoCo;
- a robotics benchmark covering task completion, collisions, near-misses, recovery and handover;
- a written certification boundary that says LAIX is advisory or task-level, not a safety function.

None of those are native features today.

## Current evidence

The current evidence is not robotics-specific:

- the live decision benchmark uses a generic 120-case corpus;
- the continuity benchmark is a synthetic mechanism test;
- there is no robot-specific benchmark or deployment result.

Before claiming robotics readiness, run a robot-specific benchmark and a real deployment. The scope of
the current evidence is in the
[evidence map](../../06-research/02-evaluation/evidence-map.md).

## Related

- [Scope and boundaries](../01-architecture/02-scope-and-boundaries.md) - core, app kit and host.
- [Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md) - approval, receipts and recovery.
- [Platform](../../03-appkit/04-connect/02-platform.md) - skills, approvals and events.
- [Stores](../../03-appkit/04-connect/01-stores.md) - state, checkpoints and outcomes.
- [Decision continuity](../../02-core/03-decision/04-history.md) - state carried into the next decision.
- [Evaluation](../../02-core/06-evaluation/01-cases.md) - cases, reports and benchmarks.
