"""Cheap detectors always run. Admit a deep call only when it pays off.

The result is:

    ('camera', 'read-page') ('full-audio',)

- camera: the cheap detector always runs.
- read-page: the deep call is admitted by gain and budget.
- full-audio: skipped because its cost exceeds the budget.
"""

from laix import Budget, ResourceScheduler, SensingOption

plan = ResourceScheduler().schedule(
    [
        SensingOption(name="camera", tier="cheap", cost=0.0),
        SensingOption(
            name="read-page",
            tier="deep",
            cost=0.1,
            latency_ms=800,
            information_gain=0.9,
        ),
        SensingOption(
            name="full-audio",
            tier="deep",
            cost=2.0,
            latency_ms=800,
            information_gain=0.9,
        ),
    ],
    budget=Budget(max_deep_calls=2, max_cost=1.0, max_latency_ms=2_000),
    uncertainty=0.8,
)

print(plan.allowed, tuple(item["name"] for item in plan.skipped))
