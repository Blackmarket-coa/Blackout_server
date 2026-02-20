# Blackout Ops Runbook

This runbook covers operating Synapse in Blackout signaling-only mode.

Related reliability and refactor tracking docs:

- [Distributed self-healing blueprint](./distributed_self_healing_blueprint.md)
- [Project completion tracker](./project_completion_tracker.md)

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


## Phone-hosted low-resource profile

Recommended baseline for constrained/mobile-hosted homeservers:

- `blackout.enabled: true`
- `blackout.signal_event_ttl: "48h"`
- `enable_search: false` and `enable_media_repo: false` (forced under blackout)
- Keep worker/background topology conservative; avoid optional heavy workers.

Capacity baseline and caveats:

- Target ~200–500 registered users and ~20–50 concurrently active peers.
- Expect battery, thermal, and network churn; plan automated restart/health checks.
- Monitor WAL/database growth and run regular backups with restore drills.

## Scalability thresholds and relay policy

Suggested operating guardrails for blackout mesh signaling:

- Room fan-out target: 20–50 active peers; introduce temporary relays above 50.
- Warning threshold: federation blackout reject rate >1% over 15m.
- Critical threshold: federation blackout reject rate >5% over 15m.
- Warning threshold: signal purge lag >15m.
- Critical threshold: signal purge lag >60m.

Temporary relay/super-peer selection guidance:

- Prefer stable, always-on nodes with low packet loss and sufficient uplink.
- Publish relay topology hints in `message_metadata.topology_hints`.
- Roll back relay assignment if reject rates or ICE failures increase for 2 consecutive windows.
