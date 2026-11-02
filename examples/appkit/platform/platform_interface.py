"""The south interface: run a skill, ask for approval, read events.

The result is:

    7 skill.started,skill.finished fast True

- 7: the skill returned the value it was given.
- skill.started,skill.finished: the platform streamed both events.
- fast: the requested capability level, not a model name.
- True: the approver allowed the action.
"""

from laix import ApprovalDecision, ApprovalRequest, InMemoryPlatform, SkillCall

platform = InMemoryPlatform(
    approver=lambda request: ApprovalDecision(approved=True, by="owner", note="ok")
)
platform.register("lookup", lambda call: call.args["value"])

result = platform.run_skill(SkillCall("lookup", {"value": 7}, trace_id="tr-1"))
kinds = ",".join(event.kind for event in platform.events("tr-1"))
approval = platform.request_approval(
    ApprovalRequest(decision_id="d-1", action_name="assign", rationale="owner asked")
)

print(result, kinds, platform.capability("fast").level, approval.approved)
