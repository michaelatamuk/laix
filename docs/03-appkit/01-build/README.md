# Build

Turn an app event into a `DecisionRequest`, get a `Decision`, and choose the policy that runs.

1. [Integration](01-integration.md) - the adapter, host confidence, rollout, manager boundary and privacy.
2. [Single decision](02-single-decision.md) - `DecisionClient`, the response, execution, delivery and status.
3. [Policies in the app](03-policies-in-the-app.md) - selection, registration, custom policies, versioning and shadow rollout.
4. [LangGraph](04-langgraph.md) - a decision node, approval interrupt, checkpointer and execution receipt.
5. [MCP server](05-mcp.md) - expose `decide` over stdio to an MCP client.
