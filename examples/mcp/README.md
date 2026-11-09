# MCP client example

Install the optional extra from the source checkout:

```powershell
python -m pip install -e "packages/python/laix[mcp]"
```

Use `client-config.json` as the MCP client entry, then call the `decide` tool with the public
`DecisionRequest` JSON. The full guide is in
[the MCP page](../../docs/03-appkit/01-build/05-mcp.md).

```json
{
  "request": {
    "subject": "invoice 4832",
    "at": "2026-11-01T10:00:00Z",
    "signals": [
      { "id": "s-1", "kind": "deadline", "severity": "high", "confidence": 0.9 }
    ],
    "context": { "now": "2026-11-01T10:00:00Z", "quiet_hours": null }
  },
  "policy": "auto"
}
```
