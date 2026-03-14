# Signaling-Only Persistence Policy

Status: Approved (BLK-101)
Owner: Backend Lead
Last updated: 2026-03-14

## Purpose

Define the canonical persistence boundaries for Blackout Server when operating in signaling-only mode.

## Scope

This policy applies when `blackout_signaling_only_mode: true`.

## Persisted data (allowed)

The server MAY persist only the minimum data required for identity, security, and room authorization:

1. **Accounts and profile metadata**
   - User IDs, account lifecycle metadata, and credentials necessary for authentication.
2. **Device identity and key material**
   - Device keys, cross-signing state, one-time/pre-key metadata required by Matrix identity/security flows.
3. **Room membership and auth-critical state**
   - State events required to evaluate authorization and maintain room membership semantics.
4. **Signaling artifacts with bounded TTL**
   - `m.blackout.signal` events and related signaling metadata required for P2P setup.

## Non-persisted data (blocked)

The server MUST NOT retain:

1. `m.room.message` payload bodies.
2. `m.room.encrypted` payload bodies.
3. Media binaries and long-lived media derivatives.
4. Search indexes over message payload content.

## Enforcement requirements

1. Write-path policy gate MUST classify incoming events as allowed or blocked.
2. Blocked content MUST return explicit typed errors.
3. Allowed signaling artifacts MUST be retained only within configured TTL windows.
4. Purged signaling artifacts MUST be irretrievable via API.

## `m.blackout.signal` schema baseline (BLK-105)

Server-side validation MUST enforce the following baseline:

- Required root field: `message_metadata`
- Required `message_metadata` fields:
  - `message_id` (non-empty string)
  - `sender_key_id` (non-empty string)
- Optional payload sections:
  - `ice_candidates`
  - `sdp_offer`
  - `sdp_answer`
  - `chunk_announcements`
  - `offline_retrieval`
  - `self_destruct_after`
- Unknown root fields are rejected.
- Invalid section shapes are rejected.

Validation is performed server-side with a JSON schema plus additional semantic checks
for chunk hash shape and redundancy metadata consistency.

## Configuration contract

- `blackout_signaling_only_mode: true|false`
- `blackout_signal_ttl_hours: <24-72>`
- `blackout_purge_interval_minutes: <positive int>`

## Migration and compatibility

1. `blackout_signaling_only_mode` MUST be feature-flag controlled for staged rollout.
2. Existing deployments MUST receive explicit migration guidance before hard enforcement.
3. Compatibility behavior for legacy Matrix clients must follow ADR outcomes from blocker decisions.

## Operational controls

- Add audit metrics for blocked event types and purge activity.
- Alert on unexpected growth in retained signaling artifacts.
- Publish weekly marker and risk status in tracker updates.

## Acceptance checklist (BLK-101)

- [x] Canonical allow/deny persistence policy documented.
- [x] Required config keys listed.
- [x] Enforcement expectations documented.
- [x] Sign-off by Backend Lead + Architecture Council.

## Sign-off record (BLK-101)

- **Decision:** Approved
- **Approver roles:** Backend Lead, Architecture Council
- **Approval date:** 2026-03-14
- **Evidence:**
  - `docs/blackout_governance_signoff_log.md` (Phase 0/Phase 1 governance approvals)
  - `docs/project_completion_tracker.md` (canonical completion and evidence linkage)
