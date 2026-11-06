# Security policy

LAIX is a decision library, not a sandbox. The host owns authentication, authorization,
network security, storage, model access and execution. The security boundary is therefore
shared: LAIX must not widen the host's attack surface, and the host must not trust inputs or
model output blindly.

## Supported versions

| Version | Supported |
|---|---|
| `0.9.x` | yes |
| older | no |

This is a pre-1.0 project. Security fixes are applied to the current minor line.

## Reporting a vulnerability

Do **not** open a public issue for a vulnerability.

Use GitHub's private vulnerability reporting:

<https://github.com/michaelatamuk/laix/security/advisories/new>

Please include:

- the affected version and package (Python, TypeScript or both);
- the affected surface (`decide`, a planner, streaming, execution, records, delivery);
- a minimal reproduction or proof of concept;
- the impact you believe is possible;
- any suggested fix or mitigation.

You will get a best-effort acknowledgement. There is no bug bounty and no formal SLA.

## In scope

- Unsafe decisions caused by malformed or hostile `DecisionRequest` data.
- A model, policy or planner output that bypasses hard constraints or approval gates.
- Audit or record tampering that `verify_record` should detect.
- Secret leakage through decisions, traces, records, delivery or logs.
- Execution issues in the app kit: duplicate actions, lost receipts, unsafe recovery.
- Dependency or packaging issues in the published packages.

## Out of scope

- Vulnerabilities in the host application, model provider or infrastructure.
- Missing authentication, authorization or transport security in the host.
- Prompt injection inside a host-owned model, except where LAIX claims to contain it.
- Denial of service caused by a host that accepts unbounded input or runs untrusted code.
- Social engineering and physical access.

## Safe harbour

We will not pursue legal action for good-faith research that follows this policy, avoids
privacy violations, does not degrade service and gives us reasonable time to fix the issue.

## More

The threat model, trust boundaries and recommended controls are in
[docs/04-concepts/security.md](docs/04-concepts/security.md).
