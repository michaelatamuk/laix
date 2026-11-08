"""Execute steps and compensate completed ones through the bridge."""

from __future__ import annotations

from laix import ActionOption, ExecutionBridge, ExecutionStep


def reserve(action, context) -> dict:
    return {"reserved": action.id}


def charge(action, context) -> dict:
    raise RuntimeError("declined")


def release(action, context) -> dict:
    return {"released": action.id}


bridge = ExecutionBridge(
    handlers={"reserve": reserve, "charge": charge},
    undo_handlers={"reserve": release},
)
result = bridge.run_steps(
    [
        ExecutionStep(ActionOption(id="a1", verb="act", name="reserve")),
        ExecutionStep(ActionOption(id="a2", verb="act", name="charge")),
    ],
    actor="checkout",
)
print(result.completed, result.compensated, result.error)
