"""Record the payment decision, approve it, then execute it.

The result is:

    executed True

That means:

- executed: the record moved from approved to executed.
- True: the record fingerprint still matches its content.

A record moves through these states:

    draft -> approved -> executed -> undone

A rejected record ends at rejected.
"""

from laix import approve_record, create_record, verify_record
from laix.record import EvidenceRef, mark_executed

record = create_record(
    title="Pay the electricity bill",
    decision="Pay 42.00 today.",
    evidence=(EvidenceRef(id="bill-1", quote="The bill is due today."),),
)
approved = approve_record(record, by="owner")
executed = mark_executed(approved, by="owner")

print(executed.status, verify_record(executed))
