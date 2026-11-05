# Delivery

The app owns the channel. LAIX defines the port and the receipt.

```python
from laix import DeliveryPort, DeliveryReceipt

class EmailDelivery:
    def deliver(self, decision, message, *, channel="default") -> DeliveryReceipt:
        ...
```

`DeliveryPort.deliver(decision, message, channel=...)` returns a `DeliveryReceipt` with status
`delivered`, `skipped` or `failed`.

`NullDelivery` is a test double that records `skipped` receipts in memory.

```python
from laix import NullDelivery

port = NullDelivery()
receipt = port.deliver(decision, "the decision", channel="email")
print(receipt.status, receipt.channel)
```

## What the app keeps

- the transport and credentials;
- the template and message content;
- the receipt store;
- retries and channel fallback.

LAIX provides the delivery decision. The app chooses the channel, template, credentials, receipt
store, retries and channel fallback.

## Examples

- Python: `examples/python/05-execute/delivery.py`
- TypeScript: `examples/typescript/05-execute/delivery.mts`
