# Blackout Blocker Decision Record (BLK-117)

Date: 2026-02-27  
Facilitator: Architecture Council

## Decisions

1. **Blocked events policy**
   - Decision: **hard reject** blocked timeline payload events (`m.room.message`, `m.room.encrypted`) with explicit `403 M_FORBIDDEN` errors.
2. **Compatibility mode for existing Matrix clients**
   - Decision: Use migration flag `blackout_signaling_only_mode` for staged rollout; default remains disabled until deployment cutover.
3. **Minimum schema for federated signaling**
   - Decision: `m.blackout.signal` requires `message_metadata.message_id` and `message_metadata.sender_key_id`, with strict server-side JSON schema validation.
4. **TURN default policy**
   - Decision: default recommendation is external `coturn`; on-device TURN is opt-in for constrained deployments.
5. **Retention default**
   - Decision: default signaling retention remains `48h` (within 24–72h policy) pending compliance review updates.

## Implementation linkage

- Write-path hard rejects for blocked payload types are implemented in local and federated ingress.
- Migration toggle alias (`blackout_signaling_only_mode`) is wired to blackout mode enablement.
- Schema validation for `m.blackout.signal` is enforced server-side before event acceptance.

## Follow-ups

- ✅ Published compatibility matrix for legacy clients: `docs/development/blackout_client_compatibility_matrix.md`.
- ✅ Published TURN policy and retention compliance artifacts: `docs/development/blackout_turn_default_policy.md`, `docs/development/blackout_retention_compliance_note.md`.
