# Blackout Server — Backend Plan Tracker

This tracker translates the **Blackout_server backend plan** into executable engineering work.

Legend:
- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked / needs decision

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

## 9) Existing code TODO/FIXME alignment map (initial seed)

These items are a seed list to connect current backlog comments to this plan.

- [ ] `faster_joins` TODO cluster (federation partial-state behavior)
  - Plan tie-in: **Scalability + reliability under constrained hosts**
- [ ] Sync TODO/FIXME cluster (`compute_state_delta`, summary behavior)
  - Plan tie-in: **Ephemeral signaling semantics + correctness**
- [ ] Storage/search/media TODO/FIXME clusters
  - Plan tie-in: **Remove message storage + disable indexing/media**
- [ ] Tracker-tagged TODOs (`TODO(owner)`)
  - Plan tie-in: **Convert owner-notes into explicit milestones and issues**

---

## 10) Decisions needed now (blockers)

- [!] Canonical behavior for blocked events: hard reject vs accept-and-drop.
- [!] Backward compatibility mode for existing Matrix clients.
- [!] Minimum schema required to keep federation semantics healthy.
- [!] Whether TURN runs on-device by default or external by policy.
- [!] Exact retention defaults (24h, 48h, or 72h) and compliance implications.

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

