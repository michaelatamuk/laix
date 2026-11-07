# Delivery

The app owns the channel. LAIX defines the port and the receipt.

## The port

```python
from laix import DeliveryPort, DeliveryReceipt

class EmailDelivery:
    def deliver(self, decision, message, *, channel="default") -> DeliveryReceipt:
        ...
```

`DeliveryPort.deliver(decision, message, channel=...)` returns a `DeliveryReceipt`.
`NullDelivery` is a test double that records `skipped` receipts in memory.

```python
from laix import NullDelivery

port = NullDelivery()
receipt = port.deliver(decision, "the decision", channel="email")
print(receipt.status, receipt.channel)
```

## The receipt

| Field | Meaning |
|---|---|
| `id` | Delivery receipt id. |
| `decision_id` | The decision that was delivered. |
| `channel` | The channel the app used. |
| `status` | `delivered`, `skipped` or `failed`. |
| `at` | When the attempt happened. |
| `detail` | App-owned result detail. |

`DELIVERY_STATUSES = ("delivered", "skipped", "failed")` is exported for validation.

## Retries and fallback

The app owns retries and channel fallback:

- retry transient transport failures;
- fall back from a primary channel to a secondary one when policy allows;
- never report `delivered` when the transport did not confirm it;
- keep the receipt id stable across retries when the same delivery is retried.

A decision can be delivered without being executed. The delivery receipt is not an execution
receipt.

## What the app keeps

- the transport and credentials;
- the template and message content;
- the receipt store;
- retries and channel fallback;
- the retention policy for delivered messages.

LAIX provides the delivery decision and the port. The app chooses the channel, template, credentials,
receipt store, retries and fallback.

## Examples

- Python: `examples/python/05-execute/delivery.py`
- TypeScript: `examples/typescript/05-execute/delivery.mts`

## TypeScript

TypeScript exports `DeliveryPort`, `DeliveryReceipt`, `DELIVERY_STATUSES` and `NullDelivery`.
`DeliveryStatus` is the status type.

## Boundary

- Delivery is not execution. A message can be delivered without changing the world.
- The app owns the transport, credentials and message content.
- The receipt is the proof of the delivery attempt, not a guarantee that a person read it.
- Keep secrets and raw customer content out of the receipt detail.

## Related

- [Single decision](../01-build/02-single-decision.md) - `DecisionClient.deliver`.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - the action receipt.
- [Platform](02-platform.md) - the execution side.
- [Deployment](../05-operate/03-deployment.md) - retention and security.
