# Benchmarks

Two different things live here:

| Folder | Kind | Contents |
|---|---|---|
| `live/` | data | the versioned decision corpus; `live/v1/` is the current, frozen corpus |
| `compare/` | harness | external-system adapters, capability matrix and optional requirements |

The corpus and the harness are separate on purpose:

- `live/v1/` holds the schema and the dev, test and adversarial splits;
- `compare/` runs the same `LiveDecisionEngine` inside external orchestration frameworks and reports
  operational overhead, not decision accuracy.

`live/v1` is the corpus version. `results/live_bench_v2/` is the current benchmark run label; it is
not a second corpus version.
