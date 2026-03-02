# Blackout Server — Backend Plan Tracker

This tracker translates the **Blackout_server backend plan** into executable engineering work.

Legend:
- [ ] Not started
- [~] In progress
- [x] Complete
- [!] Blocked / needs decision

Last updated: 2026-02-27

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

Classification legend:
- **required-now**: needed to unblock Phase 1 execution and near-term risk retirement.
- **required-later**: important, but sequenced after Phase 1 stabilization.
- **not-in-scope**: strategic target retained for roadmap, not for current execution sprints.
- **deferred-with-signoff**: explicitly deferred by approver with date, rationale, and re-evaluation trigger.

### 13.1 Open checklist items: scope classification coverage

All currently open checklist items in Sections 0-12 are classified below.

| Scope class | Open items covered | Coverage source |
|---|---:|---|
| required-now | 20 | Ticketized in Section 13.2 (`BLK-101`..`BLK-120`) |
| required-later | 6 | Section 13.3 table |
| not-in-scope | 4 | Section 13.4 table |
| deferred-with-signoff | 0 | Section 13.5 (none this pass) |

### 13.2 Required-now operational backlog (owner/date/exit/evidence)

| Ticket | Scope class | Open checklist items covered | Wave | Owner | Target sprint/date | Measurable exit criteria | Evidence path |
|---|---|---|---|---|---|---|---|
| BLK-101 | required-now | 1.1 persistence policy (what is persisted / not persisted) | Wave 1 | Backend Lead | Sprint 1 / 2026-03-14 | Canonical policy explicitly lists persisted vs non-persisted classes and is approved by Backend + Security leads. | `docs/signaling_only_persistence_policy.md`; approval note in tracker weekly update |
| BLK-102 | required-now | 1.2 write-path persistence gate + migration toggle (`blackout_signaling_only_mode`) | Wave 1 | Storage/API Engineer | Sprint 1 / 2026-03-18 | Write path rejects/discards non-allowed classes behind config flag with passing unit/integration tests. | implementation in `synapse/`; tests under `tests/`; tracker update artifact |
| BLK-103 | required-now | 1.3 disable media/index/history retrieval surfaces | Wave 1 | Platform Engineer | Sprint 1 / 2026-03-19 | Media/index/history endpoints are disabled in signaling-only mode and return stable disabled errors. | implementation in `synapse/`; API tests under `tests/`; release notes entry |
| BLK-104 | required-now | 1.4 integration + migration validation tests | Wave 2 | QA/Backend Engineer | Sprint 2 / 2026-03-26 | Integration suite proves membership continuity, payload rejection policy, and no migration corruption. | `tests/` integration suite + CI run log reference |
| BLK-105 | required-now | 2.1 `m.blackout.signal` schema/versioning + payload validation limits | Wave 1 | Protocol Engineer | Sprint 1 / 2026-03-17 | Versioned schema defines allowed classes + max payload and validator accepts/rejects deterministically. | schema doc in `docs/development/`; validator/tests in repo |
| BLK-106 | required-now | 2.2 enforcement + explicit error codes for blocked event types | Wave 1 | API Engineer | Sprint 1 / 2026-03-18 | `m.room.message` and `m.room.encrypted` are hard-blocked with stable, documented error codes. | implementation/tests in `synapse/` + `tests/`; error code doc update |
| BLK-107 | required-now | 2.3 client interop notes + conformance tests | Wave 2 | Client Liaison + QA | Sprint 2 / 2026-03-27 | Interop document covers fallback behavior and conformance fixtures pass for accept/reject matrix. | `docs/development/blackout_client_compatibility_matrix.md`; conformance tests |
| BLK-108 | required-now | 3.1 TURN model decision + secure coturn baseline | Wave 1 | Infra Lead | Sprint 1 / 2026-03-15 | ADR finalized and baseline secure coturn config committed with operator instructions. | `docs/development/blackout_turn_default_policy.md`; coturn baseline config in repo |
| BLK-109 | required-now | 3.2 NAT coordination boundaries + anti-abuse limits | Wave 2 | Security Engineer | Sprint 2 / 2026-03-28 | Signaling rate-limits and abuse thresholds are enforced and alertable. | policy doc + implementation/tests + metrics/alerts config |
| BLK-110 | required-now | 4.1 retention configs + TTL semantics | Wave 1 | Backend Lead | Sprint 1 / 2026-03-16 | TTL config keys and semantics are documented and configurable in runtime settings. | `docs/development/blackout_retention_compliance_note.md`; config docs/code |
| BLK-111 | required-now | 4.2 bounded incremental purge job + API irretrievability checks | Wave 2 | Data Lifecycle Engineer | Sprint 2 / 2026-03-29 | Purge job runs bounded batches and purged events are not retrievable through APIs. | purge implementation + integration tests + ops runbook note |
| BLK-112 | required-now | 4.3 retention safety tests (including auth-state protection) | Wave 2 | QA/Backend Engineer | Sprint 2 / 2026-03-29 | Tests verify purge keeps auth-critical state and removes only eligible signaling artifacts. | `tests/` retention safety suite |
| BLK-113 | required-now | 5.1 crypto alignment baseline (identity keys, DTLS, AES, hashing, Merkle contract) | Wave 3 | Security Architect | Sprint 3 / 2026-04-05 | Security checklist and threat-model addendum are approved and mapped to testable server contracts. | security addendum in `docs/development/`; checklist evidence |
| BLK-114 | required-now | 6 gate checklist baseline (CPU/memory, battery, churn, reconnect) | Wave 3 | Mobile Performance Engineer | Sprint 3 / 2026-04-09 | First benchmark run on representative mobile hardware reports all four gate dimensions. | benchmark report in `docs/reports/` + harness scripts |
| BLK-115 | required-now | 8 Phase 1 deliverables + Phase 1 exit criterion | Wave 3 | Program Manager + Backend Lead | Sprint 3 / 2026-04-10 | Phase 1 demo shows end-to-end peer setup without server message persistence and sign-off recorded. | demo report in `docs/reports/`; tracker gate update |
| BLK-116 | required-now | 9 marker alignment seed clusters (faster_joins/sync/storage+search+media/follow-up markers) | Wave 1 | Tech Lead | Sprint 1 / 2026-03-20 | Each cluster has a mapped issue with owner, label, and link from tracker. | issue mapping table in tracker update artifact |
| BLK-117 | required-now | 10 blocker decisions (event behavior, compat mode, min schema, TURN default, retention defaults) | Wave 1 | Architecture Council | Sprint 1 / 2026-03-14 | Decision record exists and each blocker has a final policy outcome linked from tracker. | `docs/development/blackout_blocker_decision_record_2026-02-27.md` |
| BLK-118 | required-now | Marker budget enforcement policy (canonical inventory exclusions only) | Wave 1 | Release Manager | Sprint 1 / 2026-03-14 | Marker policy doc is published and referenced by weekly update process. | `docs/marker_budget_policy.md` |
| BLK-119 | required-now | Weekly marker delta reporting in tracker updates | Wave 1 | Program Manager | Sprint 1 / 2026-03-14 | Weekly template includes opened/closed/net marker deltas and is used in current sprint report. | `docs/development/blackout_weekly_tracker_update_template.md` |
| BLK-120 | required-now | Top-hotspot owner assignment for marker debt | Wave 1 | Tech Lead | Sprint 1 / 2026-03-14 | Weekly report includes top-hotspot DRI assignment for highest-growth cluster. | `docs/development/blackout_weekly_tracker_update_template.md` |

### 13.2a Required-now implementation waves (objective deliverables)

| Wave | Objective deliverables |
|---|---|
| Wave 1 — Policy + enforcement foundation | Finalize blocker decisions/policies, ship signaling-only write-path gate + blocked-event enforcement, disable incompatible surfaces, finalize TTL/TURN defaults, and lock marker-governance cadence (`BLK-101,102,103,105,106,108,110,116,117,118,119,120`). |
| Wave 2 — Validation + safeguards | Complete integration/conformance testing, anti-abuse controls, purge implementation, and retention safety guardrails (`BLK-104,107,109,111,112`). |
| Wave 3 — Readiness + viability gates | Close crypto alignment, mobile viability baselines, and Phase 1 end-to-end exit gate (`BLK-113,114,115`). |

### 13.2b Compact wave table (item -> wave -> owner -> due)

| Item (ticket) | Wave | Owner | Due |
|---|---|---|---|
| BLK-101 | Wave 1 | Backend Lead | 2026-03-14 |
| BLK-102 | Wave 1 | Storage/API Engineer | 2026-03-18 |
| BLK-103 | Wave 1 | Platform Engineer | 2026-03-19 |
| BLK-104 | Wave 2 | QA/Backend Engineer | 2026-03-26 |
| BLK-105 | Wave 1 | Protocol Engineer | 2026-03-17 |
| BLK-106 | Wave 1 | API Engineer | 2026-03-18 |
| BLK-107 | Wave 2 | Client Liaison + QA | 2026-03-27 |
| BLK-108 | Wave 1 | Infra Lead | 2026-03-15 |
| BLK-109 | Wave 2 | Security Engineer | 2026-03-28 |
| BLK-110 | Wave 1 | Backend Lead | 2026-03-16 |
| BLK-111 | Wave 2 | Data Lifecycle Engineer | 2026-03-29 |
| BLK-112 | Wave 2 | QA/Backend Engineer | 2026-03-29 |
| BLK-113 | Wave 3 | Security Architect | 2026-04-05 |
| BLK-114 | Wave 3 | Mobile Performance Engineer | 2026-04-09 |
| BLK-115 | Wave 3 | Program Manager + Backend Lead | 2026-04-10 |
| BLK-116 | Wave 1 | Tech Lead | 2026-03-20 |
| BLK-117 | Wave 1 | Architecture Council | 2026-03-14 |
| BLK-118 | Wave 1 | Release Manager | 2026-03-14 |
| BLK-119 | Wave 1 | Program Manager | 2026-03-14 |
| BLK-120 | Wave 1 | Tech Lead | 2026-03-14 |

### 13.3 Required-later items (scope class + next action)

| Open checklist items covered | Scope class | Next action |
|---|---|---|
| 5.2 Threat handling backlog (offline retrieval, redundancy enforcement, withholding mitigation, key rotation/revocation, device compromise workflow, expiration auditability) | required-later | Create Epic `BLK-SEC-THREATS` in Sprint 4 planning with milestone-level acceptance criteria. |
| 7 Horizontal scalability validation (scheduler/queueing/partition behavior) | required-later | Schedule load-test design after Wave 3 completion. |
| 7 Vertical scalability strategy (super-peer criteria, hierarchical mesh signaling, avoid full mesh) | required-later | Run architecture spike and publish large-room control-plane RFC in PI-2 planning. |
| 8 Phase 2 deliverables + exit criterion (chunking, distributed replication, redundancy tracking) | required-later | Keep in Program Increment 2 backlog; split into design + implementation epics. |
| 8 Phase 3 deliverables + exit criterion (file swarm, Merkle validation, streaming) | required-later | Keep in Program Increment 3 with prototype gate before production commitment. |
| 8 Phase 4 deliverables + exit criterion (super-peer topology, mobile tuning, bandwidth throttling) | required-later | Keep in Program Increment 4, contingent on Phase 2/3 throughput outcomes. |

### 13.4 Not-in-scope items (current tracker window)

| Open checklist items covered | Scope class | Next action |
|---|---|---|
| 0 Program goals + success criteria (north-star outcomes) | not-in-scope | Track as outcome KPIs reviewed monthly; do not gate Waves 1-3 execution on full attainment. |
| 6 Target envelope values (200-500 users, 20-50 active peers, many small rooms) | not-in-scope | Treat as performance targets for later scale validation after signaling-only baseline completion. |
| 11 Suggested issue labels/project columns | not-in-scope | Project ops to adopt labels/columns during backlog hygiene, no implementation blocking dependency. |
| 12 Strategic outcome checkpoint (identity layer, P2P messaging, distributed storage, minimal liability, phone-hostable node, takedown resilience) | not-in-scope | Retain as quarterly strategy scorecard tracked at release-train level. |

### 13.5 Deferred-with-signoff register

No items are currently marked `deferred-with-signoff` in this tracker pass.

If a deferral is needed later, add all required metadata:
- approver
- decision date
- rationale
- re-evaluation trigger/date
- evidence path to signed decision record

### 13.6 Exit-criteria confirmation for this triage pass

- [x] Every currently open checklist item has one scope class (`required-now`, `required-later`, `not-in-scope`, or `deferred-with-signoff`).
- [x] Every `required-now` item has owner + target sprint/date + measurable exit criteria + evidence path.
- [x] Required-now work is grouped into exactly 3 implementation waves with objective deliverables.
- [x] Compact wave mapping table exists (`item -> wave -> owner -> due`).
