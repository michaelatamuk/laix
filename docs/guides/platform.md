# Platform interface

The app describes the experience. The platform runs work and reports results. LAIX decides; the
platform executes.

| Word | Meaning |
|---|---|
| **Platform** | The system below LAIX that runs skills, approvals, state and events. |
| **Skill** | A named unit of work the platform can run. |
| **Capability level** | How much power a call needs: `fast`, `balanced` or `deep`. |

## Contract

```python
from laix import ApprovalRequest, SkillCall

class MyPlatform:
    def run_skill(self, call: SkillCall): ...
    def cancel(self, run_id: str, reason: str = "") -> bool: ...
    def request_approval(self, request: ApprovalRequest): ...
    def read_state(self, key: str): ...
    def write_state(self, key: str, value): ...
    def events(self, trace_id: str): ...
    def capability(self, level: str): ...
```

| Method | Purpose |
|---|---|
| `run_skill` | run a named skill |
| `cancel` | stop a running action |
| `request_approval` | ask a person |
| `read_state` / `write_state` | keep session state |
| `events` | return events for a trace |
| `capability` | return a capability level |

Levels are `fast`, `balanced` and `deep`.

`InMemoryPlatform` is the reference implementation. A real adapter wraps openJiuwen, a cloud runtime
or another platform.

## Example

```python
from laix import InMemoryPlatform, SkillCall

platform = InMemoryPlatform()
platform.register("lookup", lambda call: {"value": 7})
result = platform.run_skill(SkillCall("lookup", {}, trace_id="tr-1"))
events = platform.events("tr-1")
```

TypeScript exports `Platform`, `InMemoryPlatform`, `SkillCall` and `ApprovalRequest`.
