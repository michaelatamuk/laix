# Schema

The schema layer turns the Python record classes into one versioned JSON Schema. It is the machine-readable
side of the decision contract.

| File | Contents |
|---|---|
| `core/schema/records.py` | `RECORDS`, `RECORD_NAMES` and the record registry |
| `core/schema/build.py` | schema generation from the dataclasses |
| `core/schema/check.py` | validation helpers |
| `core/schema/laix-v1.schema.json` | the packaged schema |

```python
from laix import RECORD_NAMES
from laix.core.schema import build_schema, dumps_schema

print(RECORD_NAMES)
schema = build_schema()
document = dumps_schema(schema)
```

`schema/check.py` validates a record document against the schema. The generated schema is committed so a
host can validate records without importing the package.

## Version axes

`SCHEMA_VERSION` is the record-shape version. It is separate from the package version, the policy version
and the attention-vector version. A record field change is a schema change; an additive field is
preferred.

## Related

- [Decision contract](../01-contract/01-decision-contract.md)
- [Records](../01-contract/03-records.md)
- [Versioning](../../05-project/03-release/01-versioning.md)
