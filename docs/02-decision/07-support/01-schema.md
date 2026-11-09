# Schema

The schema layer turns the Python record classes into one versioned JSON Schema. It is the machine-readable
side of the decision contract.

| File | Contents |
|---|---|
| `decision/schema/records.py` | `RECORDS`, `RECORD_NAMES` and the record registry |
| `decision/schema/build.py` | schema generation from the dataclasses |
| `decision/schema/check.py` | validation helpers |
| `decision/schema/laix-v1.schema.json` | the packaged schema |

```python
from laix import RECORD_NAMES
from laix.decision.schema import build_schema, dumps_schema

print(RECORD_NAMES)
schema = build_schema()
document = dumps_schema(schema)
```

`schema/check.py` validates a record document against the schema. The generated schema is committed so a
host can validate records without importing the package.

## Generate and validate

From `packages/python/laix`:

```powershell
py -c "from laix.decision.schema import write_schema; write_schema()"
```

Check that the committed file is current:

```powershell
py -m pytest tests -k schema
```

| Helper | Purpose |
|---|---|
| `RECORDS` | the ten schema record classes |
| `RECORD_NAMES` | their names in declaration order |
| `record_fields(record)` | the field names of one record |
| `build_schema()` | the schema as a dictionary |
| `dumps_schema()` | the schema as indented JSON |
| `write_schema(path=None)` | write the committed schema file |
| `check(record_name, payload)` | validate required keys, primitive types and enums |

`check()` keeps the package standard-library only. Use a full JSON Schema validator when the host needs
one.

## Version axes

`SCHEMA_VERSION` is the record-shape version. It is separate from the package version, the policy version
and the attention-vector version. A record field change is a schema change; an additive field is
preferred.

## Related

- [Decision contract](../01-contract/01-decision-contract.md)
- [Records](../01-contract/03-records.md)
- [Versioning](../../06-project/03-release/01-versioning.md)
