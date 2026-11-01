# Platform interface

The app supplies the experience. The platform runs skills, keeps session state and streams events.
LAIX asks for a **capability level** and leaves model choice to the platform.

## Contract

```python
from laix import ApprovalRequest, Platform, SkillCall

class MyPlatform:
    def run_skill(self, call: SkillCall): ...
    def cancel(self, run_id: str, reason: str = "") -> bool: ...
    def request_approval(self, request: ApprovalRequest): ...
    def read_state(self, key: str): ...
    def write_state(self, key: str, value): ...
    def events(self, trace_id: str): ...
    def capability(self, level: str): ...
```

| Need | Why |
|---|---|
| run a named skill with typed arguments | LAIX decides; the platform executes |
| cancel a running action | the situation changed |
| ask for approval | the action is destructive |
| read and write session state | experience state outlives one turn |
| stream events with trace ids | cost, latency and debugging |
| a capability level | LAIX stays portable across platforms |

Capability levels are `fast`, `balanced` and `deep`.

`InMemoryPlatform` is a reference implementation for tests and local runs. A production adapter
wraps openJiuwen, a cloud runtime or another platform.

## Division of work

The platform executes and reports. LAIX decides and records. The platform may choose the model, tool
or vendor behind a capability level.

## Example

```python
from laix import InMemoryPlatform, SkillCall

platform = InMemoryPlatform()
platform.register("lookup", lambda call: {"value": 7})
result = platform.run_skill(SkillCall("lookup", {}, trace_id="tr-1"))
events = platform.events("tr-1")
```

## TypeScript

`Platform`, `InMemoryPlatform`, `SkillCall`, `ApprovalRequest` and `Capability` are also exported from
the TypeScript package.
