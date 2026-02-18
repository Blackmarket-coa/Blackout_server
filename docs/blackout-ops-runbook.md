# Blackout Ops Runbook

This runbook covers operating Synapse in Blackout signaling-only mode.

## Enable blackout mode

1. Set the following in homeserver config:

```yaml
blackout:
  enabled: true
  signal_event_ttl: "48h"
```

2. Restart Synapse.
3. Confirm startup logs include blackout overrides for search/media settings.

## Validation checklist

- Create a `m.blackout.signal` event and verify it is accepted.
- Attempt to send `m.room.message` and verify rejection.
- Confirm counters increment:
  - `synapse_blackout_signal_events_accepted_total`
  - `synapse_blackout_event_rejections_total`
  - `synapse_blackout_signal_revoked_key_rejections_total`
  - `synapse_blackout_federation_signal_revoked_key_rejections_total`

## Federation checks

- Confirm valid federated `m.blackout.signal` PDUs are accepted.
- Confirm unsupported federated timeline types are rejected and counted in
  `synapse_blackout_federation_event_rejections_total`.

## Incident triage

### High `unsupported_timeline_type` rejections

Likely cause: non-blackout client behavior.

Actions:
- Verify client-side event type usage.
- Verify room traffic is using `m.blackout.signal` payloads.

### High `invalid_signal_content` rejections

Likely cause: protocol mismatch or malformed payload.

Actions:
- Compare payload keys with allowlist (`ice_candidates`, `sdp_offer`,
  `sdp_answer`, `message_metadata`, `chunk_announcements`).
- Check upstream peers for outdated schema.

### High revoked-device-key rejections

Likely cause: compromised device, stale sender metadata, or malicious replay.

Actions:
- Inspect `synapse_blackout_signal_revoked_key_rejections_total` and
  `synapse_blackout_federation_signal_revoked_key_rejections_total` trend lines.
- Correlate rejected user IDs/device IDs with recent logout/device-delete activity.
- If rejections are unexpected, rotate active device keys and invalidate sessions.

## Retention policy for `e2e_device_key_revocations`

Policy decision: **immutable revocation history by default**.

Rationale:
- Revocations are security-critical denylist signals.
- Re-accepting previously revoked key identifiers after TTL can re-open compromise windows.

Operational guidance:
- Keep rows indefinitely unless there is a legal/data-retention requirement forcing expiry.
- If expiry is required, use a long minimum (>= 180 days) and pair with client key rotation
  policy + audit logging.
- During DB maintenance, never bulk-delete recent revocations without incident review.

## Rollback

1. Set `blackout.enabled: false`.
2. Restart Synapse.
3. Re-enable search/media settings if required for the deployment.
