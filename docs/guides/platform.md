# Platform interface

The app describes the experience. The platform runs skills, keeps state and streams events. LAIX
asks for a capability level and does not choose the model.

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
