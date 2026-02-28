# Blackout Server — Backend Plan Tracker

This tracker translates the **Blackout_server backend plan** into executable engineering work.

Legend:
- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked / needs decision

Last updated: 2026-02-28

---

## 0) Program Goals (North Star)

- [ ] Deliver a **phone-hostable signaling-first homeserver** with minimal persistence and liability.
- [ ] Preserve Matrix-compatible identity/security primitives while shifting payload transport to P2P.
- [ ] Keep server responsibilities bounded to: accounts, keys, membership, signaling metadata, policy enforcement.

Success criteria:
- [ ] No long-term message/media payload retention on server.
- [ ] Signaling event path supports WebRTC setup and metadata flow.
- [ ] Auto-expiry and purge policy is enforced for signaling artifacts.

---

## 1) Remove Message Storage

### 1.1 Storage and persistence policy
- [ ] Define canonical policy doc for what *is* persisted:
  - [ ] User accounts
  - [ ] Device keys / cross-signing state
  - [ ] Room membership and auth-critical state
  - [ ] Signaling events (ephemeral retention window)
- [ ] Define what is *not* persisted:
  - [ ] `m.room.message` bodies
  - [ ] `m.room.encrypted` payloads
  - [ ] Media binaries
  - [ ] Search indexes

### 1.2 Homeserver behavior changes
- [ ] Add event-persistence gate in write path to reject/discard non-allowed content types.
- [ ] Ensure auth/state resolution remains intact when payload events are not persisted.
- [ ] Add config toggle for migration period:
  - [ ] `blackout_signaling_only_mode: true|false`

### 1.3 Feature disablement
- [ ] Disable media repository endpoints and background jobs.
- [ ] Disable event indexing/search paths.
- [ ] Remove/disable message history retrieval surfaces for blocked event classes.

### 1.4 Validation
- [ ] Integration test: account + membership flows still pass.
- [ ] Integration test: message events are rejected or dropped per policy.
- [ ] Migration test: existing deployments can enable mode without DB corruption.

---

## 2) Add signaling-only event type: `m.blackout.signal`

### 2.1 Spec and schema
- [ ] Define event schema/versioning for `m.blackout.signal`.
- [ ] Allowed content classes:
  - [ ] ICE candidates
  - [ ] SDP offers/answers
  - [ ] Message metadata descriptors
  - [ ] Chunk announcements
- [ ] Define max payload size and validation rules.

### 2.2 Enforcement
- [ ] Add server-side validator for `m.blackout.signal` content.
- [ ] Hard-block storage of:
  - [ ] `m.room.message`
  - [ ] `m.room.encrypted`
- [ ] Emit explicit error codes for blocked event types.

### 2.3 Interop
- [ ] Document expected client behavior/fallback.
- [ ] Add conformance tests for accepted and rejected payloads.

---

## 3) TURN/STUN service integration

### 3.1 Deployment model
- [ ] Decide primary model:
  - [ ] Embedded phone-host STUN/TURN
  - [ ] External `coturn` sidecar/recommended default
- [ ] Publish minimal secure `coturn` baseline config.

### 3.2 Server responsibility boundaries
- [ ] Server assists NAT traversal coordination only.
- [ ] Server does not relay payload by default.
- [ ] Add rate limits/abuse controls for signaling storms.

### 3.3 Ops and observability
- [ ] Add health checks for TURN/STUN dependency.
- [ ] Add metrics: setup success, candidate failure rates, relay fallback ratio.

---

## 4) Ephemeral retention (24–72h)

### 4.1 Retention policy
- [ ] Add config:
  - [ ] `blackout_signal_ttl_hours` (24–72)
  - [ ] `blackout_purge_interval_minutes`
- [ ] Define TTL semantics (based on event creation vs. receipt time).

### 4.2 Purge implementation
- [ ] Background purge job for expired signaling events.
- [ ] Ensure purge is incremental and bounded.
- [ ] Ensure purged content is irretrievable via APIs.

### 4.3 Safety
- [ ] Retention tests (unit + integration).
- [ ] Verify purge does not remove auth-critical room state.

---

## 5) Security model alignment

### 5.1 Cryptographic layers
- [ ] Matrix identity keys remain authoritative for user/device identity.
- [ ] WebRTC DTLS required for peer transport setup.
- [ ] Per-message AES payload encryption in the client protocol.
- [ ] Chunk-level hashing required.
- [ ] Merkle-root integrity verification for reconstructed objects.

### 5.2 Threat handling backlog
- [ ] Offline user retrieval strategy.
- [ ] Redundancy enforcement policy.
- [ ] Malicious peer withholding mitigation.
- [ ] Key revocation and rotation model.
- [ ] Device compromise response workflow.
- [ ] Message expiration enforcement auditability.

---

## 6) Phone-as-server viability gates

### Target envelope
- [ ] Registered users: 200–500
- [ ] Active peers: 20–50
- [ ] Many small rooms

### Gate checklist
- [ ] CPU/memory profile acceptable on representative mobile hardware.
- [ ] Battery impact within target thresholds.
- [ ] Network churn tolerance validated.
- [ ] Cold-start + reconnect time acceptable.

---

## 7) Scalability strategy

### Horizontal (many small rooms)
- [ ] Validate scheduler, queueing, and room partition behavior.

### Vertical (large rooms)
- [ ] Define super-peer election criteria.
- [ ] Prototype hierarchical mesh (tree topology) control signaling.
- [ ] Avoid full-mesh requirement in large rooms.

---

## 8) Development phases

## Phase 1 — Signaling foundation
- [ ] Metadata-only Matrix events
- [ ] WebRTC message channel
- [ ] Local message storage (client-side)

Exit criteria:
- [ ] End-to-end peer setup works without server message persistence.

## Phase 2 — Replication primitives
- [ ] Chunking system
- [ ] Distributed replication
- [ ] Redundancy tracking

Exit criteria:
- [ ] Chunk availability meets redundancy target under peer churn.

## Phase 3 — File swarm
- [ ] File swarm transport
- [ ] Merkle tree validation
- [ ] Large file P2P streaming

Exit criteria:
- [ ] Integrity verification and streaming pass at target sizes.

## Phase 4 — Scale hardening
- [ ] Super-peer topology
- [ ] Mobile performance tuning
- [ ] Bandwidth throttling

Exit criteria:
- [ ] Meets mobile viability envelope and large-room strategy goals.

---

## 9) Existing code marker alignment map (initial seed)

These items are a seed list to connect current backlog comments to this plan.

- [ ] `faster_joins` marker cluster (federation partial-state behavior)
  - Plan tie-in: **Scalability + reliability under constrained hosts**
- [ ] Sync marker cluster (`compute_state_delta`, summary behavior)
  - Plan tie-in: **Ephemeral signaling semantics + correctness**
- [ ] Storage/search/media marker clusters
  - Plan tie-in: **Remove message storage + disable indexing/media**
- [ ] Tracker-tagged follow-up markers (`TO-DO(owner)` in historical notes)
  - Plan tie-in: **Convert owner-notes into explicit milestones and issues**

---

## 10) Decisions needed now (blockers)

- [!] Canonical behavior for blocked events: hard reject vs accept-and-drop.
- [!] Backward compatibility mode for existing Matrix clients.
- [!] Minimum schema required to keep federation semantics healthy.
- [!] Whether TURN runs on-device by default or external by policy.
- [!] Exact retention defaults (24h, 48h, or 72h) and compliance implications.

---

### 10.1) Implementation sequence (recommended order)

This section translates the checklist into a practical build order that minimizes rework.

1. **Finalize policy + decisions**
   - Resolve section 10 blockers.
   - Lock persistence policy from sections 1.1 and 2.1.
2. **Introduce signaling-only enforcement in write path**
   - Implement event gate and validator (sections 1.2 and 2.2).
   - Add explicit error codes for blocked types.
3. **Disable incompatible subsystems**
   - Media, indexing, message-history retrieval (section 1.3).
4. **Ship retention + purge mechanics**
   - Config, purge worker, and safety checks (section 4).
5. **Integrate TURN/STUN and operational visibility**
   - Deployment defaults, health checks, and metrics (section 3).
6. **Run viability + scale gates**
   - Phone-host envelope and topology strategy validation (sections 6 and 7).

---

### 10.2) Immediate sprint slice (first deliverable)

Goal: deliver a safe, test-backed MVP of signaling-only mode.

- [ ] Add config flag `blackout_signaling_only_mode` with default and docs.
- [ ] Gate event persistence to allow only auth-critical + `m.blackout.signal`.
- [ ] Reject `m.room.message` and `m.room.encrypted` with stable error codes.
- [ ] Disable media and search entry points behind the same mode flag.
- [ ] Add integration tests for:
  - [ ] membership/auth state unaffected
  - [ ] blocked payload events return expected errors
  - [ ] accepted signaling events are persisted and sync-visible

---

## 11) Suggested issue labels / project columns

Labels:
- `blackout:phase1`
- `blackout:phase2`
- `blackout:phase3`
- `blackout:phase4`
- `blackout:signaling-only`
- `blackout:retention`
- `blackout:security`
- `blackout:mobile-hosting`

Project columns:
- Planned
- Design Ready
- In Progress
- Blocked
- Validation
- Done

---

## 12) Strategic outcome checkpoint

- [ ] Matrix-based identity layer
- [ ] P2P encrypted messaging
- [ ] Distributed file storage
- [ ] Minimal server liability
- [ ] Phone-hostable signaling node
- [ ] Takedown-resilient architecture



---

## 13) Backlog necessity triage (unchecked items)

This section is the authoritative scope-class mapping for **every currently open checklist item** in Sections 0-12.

Scope classes:
- `required-now`
- `required-later`
- `not-in-scope`

### 13.1 Scope-class mapping rules (applies to all open checklist bullets)

| Open checklist location | Scope class |
|---|---|
| Section 0 Program Goals + Success criteria (`## 0`) | `not-in-scope` |
| Section 1 Remove Message Storage (`## 1`, all subsections) | `required-later` |
| Section 2 `m.blackout.signal` spec/enforcement/interop (`## 2`) | `required-later` |
| Section 3 TURN/STUN integration (`## 3`) | `required-later` |
| Section 4 Ephemeral retention (`## 4`) | `required-later` |
| Section 5 Security model alignment (`## 5`) | `required-later` |
| Section 6 Phone-as-server viability gates (`## 6`) | `required-later` |
| Section 7 Scalability strategy (`## 7`) | `required-later` |
| Section 8 Development phases (`## 8`) | `required-later` |
| Section 9 Existing code marker alignment map (`## 9`) | `required-later` |
| Section 10 Decisions needed now (all `[!]` blockers in `## 10`) | `required-now` |
| Section 10.2 Immediate sprint slice (all bullets/sub-bullets) | `required-now` |
| Section 12 Strategic outcome checkpoint (`## 12`) | `not-in-scope` |

### 13.2 Required-now operationalization (owner/date/exit/evidence)

| Required-now item | Owner | Target sprint/date | Measurable exit criteria | Evidence path |
|---|---|---|---|---|
| 10. Blocker: canonical blocked-event behavior (`hard reject` vs `accept-and-drop`) | Architecture Council | Sprint 1 / 2026-03-05 | ADR explicitly records the selected behavior and all APIs return one consistent behavior in tests. | `docs/development/blackout_blocker_decision_record_2026-02-27.md`, `tests/` (blocked-event behavior tests) |
| 10. Blocker: backward-compatibility mode for existing Matrix clients | Client Liaison + Backend Lead | Sprint 1 / 2026-03-06 | Compatibility matrix approved and at least one migration mode documented with expected client outcomes. | `docs/development/blackout_client_compatibility_matrix.md` |
| 10. Blocker: minimum federation-safe signaling schema | Protocol Engineer | Sprint 1 / 2026-03-06 | Minimum required fields are documented and conformance fixtures include pass/fail examples. | `docs/development/blackout_federation_schema_minimum.md`, `tests/` (schema conformance fixtures) |
| 10. Blocker: TURN default policy (on-device vs external) | Infra Lead | Sprint 1 / 2026-03-07 | Default policy + fallback policy are documented and linked from deployment guidance. | `docs/development/blackout_turn_default_policy.md` |
| 10. Blocker: retention default (24/48/72h) + compliance implications | Backend Lead + Security Architect | Sprint 1 / 2026-03-07 | Default TTL and compliance rationale are documented with explicit operational recommendation. | `docs/development/blackout_retention_compliance_note.md` |
| 10.2 Add config flag `blackout_signaling_only_mode` with default and docs | Storage/API Engineer | Sprint 1 / 2026-03-08 | Config key exists, has default, and is documented in operator docs. | `docs/signaling_only_persistence_policy.md`, relevant config/docs files |
| 10.2 Gate persistence to allow only auth-critical + `m.blackout.signal` | Storage/API Engineer | Sprint 1 / 2026-03-11 | Integration tests show blocked payload types are not persisted while auth-critical state remains persisted. | server write-path implementation files, integration tests under `tests/` |
| 10.2 Reject `m.room.message` + `m.room.encrypted` with stable error codes | API Engineer | Sprint 1 / 2026-03-11 | API responses return documented stable error codes for both blocked event types. | API handler code + `tests/` for error-code assertions |
| 10.2 Disable media and search entry points behind same mode flag | Platform Engineer | Sprint 1 / 2026-03-12 | Media/search endpoints are disabled when mode flag is enabled and regression tests verify behavior. | endpoint implementation files + tests under `tests/` |
| 10.2 Add integration test bundle (parent checklist item) | QA/Backend Engineer | Sprint 1 / 2026-03-12 | Test plan document lists the three required integration assertions and CI includes the new suite. | integration test plan + `tests/` execution output |
| 10.2 Integration tests: membership/auth unaffected | QA/Backend Engineer | Sprint 1 / 2026-03-12 | Integration suite passes proving membership/auth flows still succeed in signaling-only mode. | integration tests under `tests/` |
| 10.2 Integration tests: blocked payload events return expected errors | QA/Backend Engineer | Sprint 1 / 2026-03-12 | Tests assert expected error code matrix for blocked payload event classes. | integration tests under `tests/` |
| 10.2 Integration tests: accepted signaling events persisted + sync-visible | QA/Backend Engineer | Sprint 1 / 2026-03-12 | Tests prove `m.blackout.signal` events persist and are visible to eligible sync clients. | integration tests under `tests/` |

Deferred-with-signoff usage in this pass:
- None. No open item was re-labeled as `deferred-with-signoff` in this tracker update.

### 13.3 Required-now implementation waves (objective deliverables)

| Wave | Objective deliverables |
|---|---|
| Wave 1 — Policy lock and architecture decisions | Finalize all five Section 10 blocker decisions with committed decision artifacts and linked implementation guidance. |
| Wave 2 — Signaling-only enforcement slice | Implement mode flag, write-path gate, stable blocked-event errors, and media/search disablement behind the same flag. |
| Wave 3 — Verification and readiness gate | Land integration coverage for auth/membership continuity, blocked-event error behavior, and accepted signaling event visibility in sync. |

### 13.4 Compact wave table (`item -> wave -> owner -> due`)

| Item | Wave | Owner | Due |
|---|---|---|---|
| 10 blocked-event behavior decision | Wave 1 | Architecture Council | 2026-03-05 |
| 10 client compatibility decision | Wave 1 | Client Liaison + Backend Lead | 2026-03-06 |
| 10 federation-safe schema decision | Wave 1 | Protocol Engineer | 2026-03-06 |
| 10 TURN default policy decision | Wave 1 | Infra Lead | 2026-03-07 |
| 10 retention default decision | Wave 1 | Backend Lead + Security Architect | 2026-03-07 |
| 10.2 signaling-only mode flag | Wave 2 | Storage/API Engineer | 2026-03-08 |
| 10.2 persistence gate | Wave 2 | Storage/API Engineer | 2026-03-11 |
| 10.2 stable blocked-event errors | Wave 2 | API Engineer | 2026-03-11 |
| 10.2 media/search disablement | Wave 2 | Platform Engineer | 2026-03-12 |
| 10.2 integration test bundle (parent item) | Wave 3 | QA/Backend Engineer | 2026-03-12 |
| 10.2 integration: membership/auth unaffected | Wave 3 | QA/Backend Engineer | 2026-03-12 |
| 10.2 integration: blocked payload errors | Wave 3 | QA/Backend Engineer | 2026-03-12 |
| 10.2 integration: accepted signaling persisted + sync-visible | Wave 3 | QA/Backend Engineer | 2026-03-12 |

### 13.5 Triage pass validation checklist

- [x] Every currently open checklist item in Sections 0-12 has one scope class assigned through Section 13.1 mapping rules.
- [x] Every `required-now` item has owner + target sprint/date + measurable exit criteria + evidence path.
- [x] Required-now items are grouped into three implementation waves with objective deliverables.
- [x] Compact wave table maps `item -> wave -> owner -> due`.
