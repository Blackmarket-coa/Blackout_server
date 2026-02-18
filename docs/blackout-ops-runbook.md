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

### High purge lag / expired signal backlog

Likely cause: background expiry processing is behind, or workers are not running expected tasks.

Actions:
- Check that `enable_ephemeral_messages` is enabled on blackout nodes.
- Track age of oldest row in `event_expiry` and alert when backlog age exceeds the configured TTL window.
- Verify the purge metric `synapse_blackout_signal_events_purged_total` continues to increase over time.
- Check worker placement and DB latency if purge throughput drops.

### TURN relay failures

Likely cause: coturn misconfiguration, secret mismatch, or firewall/port exhaustion.

Actions:
- Verify `turn_shared_secret` in Synapse matches TURN server shared secret exactly.
- Validate UDP/TCP listener ports and relay port-range firewall rules.
- Check coturn logs for auth failures and relay allocation errors.
- Confirm clients can fetch TURN credentials from `/_matrix/client/r0/voip/turnServer`.

## Staging/CI validation before production

Because local environments may miss package metadata or Docker tooling, require reproducible validation in CI/staging:

- Run targeted federation blackout tests (`tests/test_federation.py`, `tests/handlers/test_federation_event.py`).
- Run blackout metric tests (`tests/storage/test_event_metrics.py`).
- Validate TURN compose profile with `docker compose -f docker/compose.turn.yaml config` and a staging smoke call.
- Confirm purge metrics and federation rejection metrics on dashboards before rollout.

## Rollback

1. Set `blackout.enabled: false`.
2. Restart Synapse.
3. Re-enable search/media settings if required for the deployment.
