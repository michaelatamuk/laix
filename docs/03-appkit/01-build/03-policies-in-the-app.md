# Policies in the app

A policy is the chooser. The core defines the policy contract; the app chooses which policy a
`DecisionClient` uses, when it changes and how it is rolled out.

The contract is small:

```python
class DecisionPolicy:
    name: str

    def decide(self, request):
        ...
```

The core policy page covers the built-in policies, the decision classes and the wrappers:
[Policies](../../02-core/03-decision/01-single/05-policies.md).

## The default path

`DecisionClient()` uses the core dispatch rule:

- a request with signals and context goes to signal attention;
- a request with a situation and options goes to the action policy;
- an explicit `policy=` always wins.

You do not register the built-in path. It is the fallback.

## Pass a policy

```python
from laix import DecisionClient

layer = DecisionClient(policy=my_policy)
decision = layer.decide(request)[0]
```

The layer registers the policy under `my_policy.name` and uses it for every decision.

## Register and select

The registry lets one app keep several policies and switch between them:

```python
layer = DecisionClient()
layer.register_policy("quality", QualityPolicy())
layer.register_policy("fast", FastPolicy())

layer.use_policy("fast")
decision = layer.decide(request)[0]

print(layer.policies())   # ('fast', 'quality')
print(layer.status())     # includes the selected policy and version
```

`register_policy` rejects an empty name or an object without `decide`. `use_policy` raises a
`DecisionPolicyError` for an unknown name and lists the registered names in the message.

## A custom policy

A policy returns one or more decisions in the public shape:

```python
from laix import Decision, DecisionClient

class QualityPolicy:
    name = "quality"
    version = "0.11.0"

    def decide(self, request):
        return [
            Decision(
                verb="guide",
                confidence=0.8,
                reason_code="policy_rule",
                rationale="open a watch",
            )
        ]

layer = DecisionClient(policy=QualityPolicy())
```

A custom policy still has to return the same `Decision` shape. The app should not invent verbs or
reason codes that the rest of the system cannot branch on.

## Versioning and rollout

`Decision` carries `policy_version`. Keep the name and the version on the policy object, and record
both with the decision. A policy change is a deployable change, not a silent edit.

For a safe rollout, wrap the new policy in `ShadowPolicy`:

```python
from laix import DecisionClient, ShadowPolicy

shadow = ShadowPolicy(primary=current_policy, shadow=candidate_policy)
layer = DecisionClient(policy=shadow)

# Every call returns the primary decision and records a difference when the
# verb, action or reason code disagrees.
print(shadow.differences)
```

Review the differences, then move traffic to the candidate. The same pattern supports a canary and a
pinned rollback version. See [Deployment](../05-operate/03-deployment.md#rollout).

## TypeScript

```ts
import { DecisionClient } from "laix";

const layer = new DecisionClient({ policy: myPolicy });
layer.registerPolicy("quality", qualityPolicy);
layer.usePolicy("quality");
console.log(layer.policies());
```

## Boundary

- The core owns the policy contract, the built-in policies and the reason codes.
- The app owns which policy runs, when it changes and how it is rolled out.
- A learned policy is still a policy; see [Outcome learning](../../02-core/02-domain/03-outcomes.md).
- Do not hide a policy switch inside the adapter. Make it explicit and versioned.

## Related

- [Integration](01-integration.md) - the adapter around the call.
- [DecisionClient](02-single-decision.md) - `DecisionClient` and the one-shot surface.
- [Policies](../../02-core/03-decision/01-single/05-policies.md) - the contract, the decision classes and the wrappers.
- [Deployment](../05-operate/03-deployment.md) - rollout and rollback.
