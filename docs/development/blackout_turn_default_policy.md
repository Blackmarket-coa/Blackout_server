# Blackout TURN Default Policy Recommendation

Date: 2026-02-27  
Owner: Infra Lead

## Decision

Default recommendation for blackout deployments is **external `coturn`**.

On-device TURN is **opt-in** and should be used only for constrained or single-node scenarios where operators accept lower reliability and tighter resource envelopes.

## Rationale

- External TURN reduces resource contention on phone-hosted homeserver nodes.
- External TURN allows independent scaling, hardening, and observability.
- Keeps signaling-plane and relay-plane operational concerns separated.

## Implementation guidance

1. Use standard TURN integration guidance (`docs/turn-howto.md`, `docs/setup/turn/coturn.md`).
2. Document deployment profile in environment runbooks.
3. Include health checks and alerting for TURN availability in blackout ops monitoring.
