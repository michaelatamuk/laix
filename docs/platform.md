# Platform interface

LAIX needs a small south interface. The app supplies the experience. The platform runs skills,
keeps session state and streams events. LAIX names a **capability level**, never a model name.

## Contract

```python
from laix import Platform, SkillCall, ApprovalRequest

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
`InMemoryPlatform` is a reference implementation for tests and local runs.
A real adapter wraps openJiuwen, a cloud runtime or another platform.

## Boundary

The platform does not decide. It runs and reports. LAIX does not know model names, tool names or
vendor endpoints.

## Example

```python
from laix import InMemoryPlatform, SkillCall

platform = InMemoryPlatform()
platform.register("lookup", lambda call: {"value": 7})
result = platform.run_skill(SkillCall("lookup", {}, trace_id="tr-1"))
events = platform.events("tr-1")
```
