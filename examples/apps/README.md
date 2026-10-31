# Caller examples

Four working apps call the same `Layer`. Each one keeps its own adapter, storage and UI. The layer
receives a generic request and returns a generic decision.

| App | What it keeps | What it sends | Result |
|---|---|---|---|
| CUE | show store, risk detection, delivery | one risk as `Signal` + `Context` | `guide worth_surfacing 75.0` |
| GeoResponse | alert store, imagery, analyst roster | one alert as `Situation` + `Action` options | `act policy_rule assign-owner True` |
| RECALL | capture, transcript, meeting links | one promise as `Signal` + `Context`, then a record | `guide worth_surfacing approved` |
| RootCause | line, case, baseline, report | one reading as `Situation` + `Action` options | `guide policy_rule open-watch` |

Run them from the repository root:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
py examples/apps/cue.py
py examples/apps/georesponse.py
py examples/apps/recall.py
py examples/apps/rootcause.py
```

## What each call means

### CUE

The production office has a power plan below the required load, due in three days. LAIX says
`guide`: show the risk now. The office decides what to change.

### GeoResponse

A change alert is confirmed with high confidence. LAIX says `act`: assign an analyst now. The
assignment needs a person's approval, so `requires_approval` is true.

### RECALL

A promise to send a contract is due in three days. LAIX says `guide`: show the promise to the user.
RECALL then records the owner's approval.

### RootCause

A quality reading is above its baseline, with medium urgency. LAIX says `guide`: open a watch for the
engineer. The engineer chooses when to look.

## Where app names belong

App names appear here, in the examples. The layer package uses generic vocabulary and contains no
app adapter.
