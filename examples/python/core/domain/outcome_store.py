"""Record what a decision changed, not a click.

The result is:

    helped -2.0 1

- helped: the metric moved in the improving direction.
- -2.0: the measured change.
- 1: the number of attributed outcomes labelled helped.
"""

from laix import Outcome, OutcomeLedger

ledger = OutcomeLedger()
ledger.add(
    Outcome(
        id="o-1",
        decision_id="d-1",
        metric="time_to_assessment",
        before=10.0,
        after=8.0,
        delta=-2.0,
        label="helped",
        attributed=True,
        direction="lower-better",
    )
)

summary = ledger.summary()
print(ledger.for_decision("d-1")[0].label, ledger.all()[0].delta, summary["helped"])
