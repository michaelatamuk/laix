# MCP server

The optional MCP server exposes one tool, `decide`, over the Model Context Protocol. It uses stdio,
so the MCP client owns the process and no network listener is opened.

| Piece | Owner |
|---|---|
| Process, transport and client connection | The MCP client |
| Request JSON and tool arguments | The MCP client |
| Verb, reason, confidence, score and approval flag | LAIX |
| Execution of the chosen action | The host, not the MCP server |

The server returns decisions only. It does not execute, deliver or store them.

## Install

From a source checkout:

```powershell
python -m pip install -e "packages/python/laix[mcp]"
```

When the package is published to PyPI, the shorter form is:

```powershell
python -m pip install "laix[mcp]"
```

The decision package stays dependency-free; `mcp>=2,<3` is an optional extra.

## Run

```powershell
laix-mcp
```

Or from a source checkout:

```powershell
python -m laix.appkit.mcp_server
```

The transport is stdio. Point an MCP client at the command:

```json
{
  "mcpServers": {
    "laix": {
      "command": "laix-mcp"
    }
  }
}
```

## The `decide` tool

| Argument | Meaning |
|---|---|
| `request` | The public request JSON. Required. |
| `policy` | `auto` (default) or `live`. |

- `auto` uses the decision dispatch: signal attention for signals and context, action selection for a
  situation and options.
- `live` puts `LiveCompositePlanner` behind `PlannerPolicy`.

### Signal request

```json
{
  "request": {
    "subject": "invoice 4832",
    "at": "2026-11-01T10:00:00Z",
    "signals": [
      {
        "id": "s-1",
        "kind": "deadline",
        "severity": "high",
        "confidence": 0.9
      }
    ],
    "context": {
      "now": "2026-11-01T10:00:00Z",
      "quiet_hours": null
    }
  },
  "policy": "auto"
}
```

### Action request

```json
{
  "request": {
    "subject": "leaking sink",
    "at": "2026-11-01T10:00:00Z",
    "situation": {
      "id": "situation-1",
      "at": "2026-11-01T10:00:00Z",
      "subject": "leaking sink",
      "beliefs": [
        {
          "id": "b-1",
          "proposition": "water is leaking",
          "confidence": 0.9
        }
      ]
    },
    "options": [
      {
        "id": "valve",
        "verb": "act",
        "name": "close the valve",
        "expected_benefit": 0.9,
        "risk": 0.1,
        "reversible": true
      }
    ]
  },
  "policy": "auto"
}
```

The response is JSON:

```json
{
  "decisions": [
    {
      "verb": "act",
      "reason_code": "policy_rule",
      "action_id": "valve",
      "confidence": 0.9,
      "requires_approval": false
    }
  ]
}
```

## Request fields

The server accepts the public `DecisionRequest` JSON:

- `subject`, `at`;
- `situation`: `id`, `at`, `subject`, `observations`, `beliefs`, `goals`, `constraints`, `phase`,
  `horizon`, `attributes`;
- `options`: `ActionOption` fields;
- `signals`: `Signal` fields;
- `context`: `now`, `quiet_hours`, `stopped`, `min_severity`, `min_confidence`, `muted_kinds`,
  `signal_interruption_budget`, `sent`, `feedback`, `escalate_after_hours`, `learned`, `allow_act`;
- `attributes`, `confidence`, `confidence_source`, `calibrated`, `deadline`, `valid_until`,
  `event_id`, `target`, `recipients`.

The full field lists are in the [decision contract](../../02-decision/01-contract/01-decision-contract.md).
Unknown top-level fields are ignored. Invalid required fields raise a tool error.

## Security and limits

- Stdio only. There is no HTTP listener, authentication layer or multi-tenant boundary.
- The server does not execute actions, open databases or deliver messages.
- The MCP client controls which tools a model can call and what request content it can see.
- Keep secrets and raw customer content out of the request and out of the tool result.
- The server is Python-only. The TypeScript package does not ship an MCP server.

## Related

- [LangGraph](04-langgraph.md) - a graph that pauses for approval.
- [A2A and OpenAPI](06-a2a.md) - the agent card and host action profile.
- [Execution and recovery](../03-execute/01-execution-and-recovery.md) - execute the returned action.
- [Reason codes](../../02-decision/01-contract/05-reason-codes.md) - the stable branch keys.
- [Deployment](../05-operate/03-deployment.md) - production deployment.
