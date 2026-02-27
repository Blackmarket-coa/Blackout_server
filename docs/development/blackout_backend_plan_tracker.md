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
- **Required-now**: needed to unblock Phase 1 execution and near-term risk retirement.
- **Required-later**: important, but sequenced after Phase 1 stabilization.
- **Not-in-scope (current tracker window)**: strategic target retained for roadmap, not for current execution sprints.

### 13.1 Required-now (with ticket mapping, owner, target sprint)

Execution artifacts created in this pass:
- `docs/signaling_only_persistence_policy.md` (BLK-101)
- `docs/marker_budget_policy.md` (BLK-118)
- `docs/development/blackout_weekly_tracker_update_template.md` (BLK-119, BLK-120)

| Ticket | Unchecked tracker bullets covered | Owner | Target sprint | Next action |
|---|---|---|---|---|
| BLK-101 | 1.1 persistence policy (what is persisted / not persisted) | Backend Lead | Sprint 1 | ✅ Drafted `docs/signaling_only_persistence_policy.md`; pending sign-off and implementation linkage. |
| BLK-102 | 1.2 write-path persistence gate + migration toggle (`blackout_signaling_only_mode`) | Storage/API Engineer | Sprint 1 | Implement gate behind config flag and add migration guardrails. |
| BLK-103 | 1.3 disable media/index/history retrieval surfaces | Platform Engineer | Sprint 1 | Add feature flags to disable endpoints/jobs and return explicit disabled errors. |
| BLK-104 | 1.4 integration + migration validation tests | QA/Backend Engineer | Sprint 2 | Add integration suite for membership continuity and payload rejection behavior. |
| BLK-105 | 2.1 `m.blackout.signal` schema/versioning + payload validation limits | Protocol Engineer | Sprint 1 | Publish schema in docs and add server-side JSON schema validator. |
| BLK-106 | 2.2 enforcement + explicit error codes for blocked event types | API Engineer | Sprint 1 | Add typed rejection paths for `m.room.message` / `m.room.encrypted`. |
| BLK-107 | 2.3 client interop notes + conformance tests | Client Liaison + QA | Sprint 2 | Author client fallback guidance and add conformance fixtures for accept/reject matrix. |
| BLK-108 | 3.1 TURN model decision + secure coturn baseline | Infra Lead | Sprint 1 | Run architecture decision record (ADR) and commit baseline coturn config template. |
| BLK-109 | 3.2 NAT coordination boundaries + anti-abuse limits | Security Engineer | Sprint 2 | Define and implement signaling rate limits and abuse budget thresholds. |
| BLK-110 | 4.1 retention configs + TTL semantics | Backend Lead | Sprint 1 | Finalize default TTL semantics (creation vs receipt) and expose config docs. |
| BLK-111 | 4.2 bounded incremental purge job + API irretrievability checks | Data Lifecycle Engineer | Sprint 2 | Implement purge scheduler with bounded batch sizes and post-purge fetch denial tests. |
| BLK-112 | 4.3 retention safety tests (including auth-state protection) | QA/Backend Engineer | Sprint 2 | Add regression tests verifying auth-critical state survives purge. |
| BLK-113 | 5.1 crypto alignment baseline (identity keys, DTLS, AES, hashing, Merkle verification contract) | Security Architect | Sprint 2 | Produce threat-model addendum and protocol acceptance checklist for Phase 1. |
| BLK-114 | 6 gate checklist baseline (CPU/memory, battery, churn, reconnect) | Mobile Performance Engineer | Sprint 3 | Define benchmark harness and collect first representative mobile baseline. |
| BLK-115 | 8 Phase 1 deliverables + Phase 1 exit criterion | Program Manager + Backend Lead | Sprint 1-2 | Convert Phase 1 bullets to sprint stories and run end-to-end demo gate. |
| BLK-116 | 9 alignment seed: `faster_joins`, sync marker clusters, storage/search/media marker clusters, tracker-tagged follow-up markers | Tech Lead | Sprint 1 | Open mapped issues for each marker cluster and attach `blackout:*` labels. |
| BLK-117 | 10 blocker decisions (hard reject vs drop, compatibility mode, minimum schema, TURN default policy, retention defaults) | Architecture Council | Sprint 1 | Hold decision workshop and record resolutions in ADR set before feature merge. |


### 13.1a Marker debt compliance gate (required-now policy)

Marker governance for tracker updates is enforced as follows:
- **Retain marker budget enforcement using canonical inventory exclusions only** (no ad-hoc exclusions by team or sprint).
- **Require weekly marker delta reporting** (`opened`, `closed`, `net`) for the tracked marker inventory.
- **Require top-hotspot owner assignment** each week for the highest-growth marker cluster.

Required-now ticket mapping for compliance gate:

| Ticket | Unchecked tracker bullets covered | Owner | Target sprint | Next action |
|---|---|---|---|---|
| BLK-118 | Marker budget enforcement policy (canonical inventory exclusions only) | Release Manager | Sprint 1 | ✅ Published `docs/marker_budget_policy.md` with canonical exclusion list and reporting requirements. |
| BLK-119 | Weekly marker delta reporting in tracker updates | Program Manager | Sprint 1 | ✅ Added weekly tracker template: `docs/development/blackout_weekly_tracker_update_template.md`. |
| BLK-120 | Top-hotspot owner assignment for marker debt | Tech Lead | Sprint 1 | ✅ Added top-hotspot DRI section to `docs/development/blackout_weekly_tracker_update_template.md`. |

### 13.2 Required-later (explicit next action)

| Unchecked tracker bullets covered | Classification | Next action |
|---|---|---|
| 5.2 Threat handling backlog (offline retrieval, redundancy enforcement, withholding mitigation, key rotation/revocation, device compromise workflow, expiration auditability) | Required-later | Create Epic `BLK-SEC-THREATS` in Sprint 3 planning with milestone-level acceptance criteria. |
| 7 Horizontal scalability validation (scheduler/queueing/partition behavior) | Required-later | Schedule load-test design in Sprint 4 after signaling-only path stabilizes. |
| 7 Vertical scalability strategy (super-peer criteria, hierarchical mesh signaling, avoid full mesh) | Required-later | Run architecture spike in Sprint 4 and publish large-room control-plane RFC. |
| 8 Phase 2 deliverables + exit criterion (chunking, distributed replication, redundancy tracking) | Required-later | Keep in Program Increment 2 backlog; split into design + implementation epics. |
| 8 Phase 3 deliverables + exit criterion (file swarm, Merkle validation, streaming) | Required-later | Keep in Program Increment 3 with prototype gate before production commitment. |
| 8 Phase 4 deliverables + exit criterion (super-peer topology, mobile tuning, bandwidth throttling) | Required-later | Keep in Program Increment 4, contingent on Phase 2/3 throughput outcomes. |

### 13.3 Not-in-scope (current tracker window; explicit next action)

| Unchecked tracker bullets covered | Classification | Next action |
|---|---|---|
| 0 Program goals + success criteria (north-star outcomes) | Not-in-scope (execution window) | Track as outcome KPIs reviewed monthly; do not gate Sprint 1-2 delivery on full attainment. |
| 6 Target envelope values (200-500 users, 20-50 active peers, many small rooms) | Not-in-scope (execution window) | Treat as performance targets for later scale validation after baseline feature completion. |
| 11 Suggested issue labels/project columns | Not-in-scope (engineering execution) | Project ops to adopt labels/columns during normal backlog hygiene, no blocking dependency. |
| 12 Strategic outcome checkpoint (identity layer, P2P messaging, distributed storage, minimal liability, phone-hostable node, takedown resilience) | Not-in-scope (current sprints) | Retain as quarterly strategy scorecard tracked at release-train level. |


### 13.4 Publish cadence artifacts (weekly tracker update)

#### Open-item count by scope class

| Scope class | Open item count | Source |
|---|---:|---|
| Required-now | 20 (4 documentation artifacts delivered; implementation tickets still open) | Tickets `BLK-101`..`BLK-120` in Sections 13.1 + 13.1a |
| Required-later | 6 | Rows in Section 13.2 |
| Not-in-scope | 4 | Rows in Section 13.3 |

#### Marker delta (week-over-week) + top-10 hotspot ownership

| Metric | Previous week | Current week | Delta | Status |
|---|---:|---:|---:|---|
| Markers opened | 0 | 0 | 0 | Stable |
| Markers closed | 0 | 0 | 0 | Stable |
| Net marker change | 0 | 0 | 0 | Stable/downward gate satisfied |

| Rank | Hotspot cluster | Owner (DRI) | WoW marker delta | Update |
|---:|---|---|---:|---|
| 1 | `faster_joins` marker cluster | Tech Lead | 0 | Owner confirmed; mitigation plan tracked in BLK-116. |
| 2 | Sync marker cluster (`compute_state_delta`, summary behavior) | API Engineer | 0 | Owner confirmed; conformance scope in BLK-107. |
| 3 | Storage/search/media marker cluster | Platform Engineer | 0 | Owner confirmed; disablement work tracked in BLK-103. |
| 4 | Tracker-tagged follow-up markers | Program Manager | 0 | Owner confirmed; conversion workflow tracked in BLK-116. |
| 5 | Signaling schema validation markers | Protocol Engineer | 0 | Owner confirmed; validator work in BLK-105. |
| 6 | Blocked-event enforcement markers | API Engineer | 0 | Owner confirmed; enforcement work in BLK-106. |
| 7 | Retention purge implementation markers | Data Lifecycle Engineer | 0 | Owner confirmed; purge work in BLK-111. |
| 8 | Retention safety test markers | QA/Backend Engineer | 0 | Owner confirmed; coverage work in BLK-112. |
| 9 | TURN/STUN integration markers | Infra Lead | 0 | Owner confirmed; ADR/config work in BLK-108. |
| 10 | Mobile viability benchmark markers | Mobile Performance Engineer | 0 | Owner confirmed; baseline work in BLK-114. |

#### Blockers, owner, and next action date

| Blocker | Owner | Next action | Next action date |
|---|---|---|---|
| Canonical behavior for blocked events: hard reject vs accept-and-drop | Architecture Council | Finalize decision in architecture review and publish ADR. | 2026-02-27 |
| Backward compatibility mode for existing Matrix clients | Client Liaison + Backend Lead | Publish compatibility matrix and migration recommendation. | 2026-02-27 |
| Minimum schema required to keep federation semantics healthy | Protocol Engineer | Submit minimum schema proposal with federation test cases. | 2026-02-27 |
| Whether TURN runs on-device by default or external by policy | Infra Lead | Present cost/reliability tradeoff memo and recommended default. | 2026-02-27 |
| Exact retention defaults (24h, 48h, or 72h) and compliance implications | Backend Lead + Security Architect | Finalize default retention setting and compliance note. | 2026-02-27 |

### 13.5 Exit-criteria confirmation for this triage pass

- [x] All unchecked bullets in Sections 0-12 are classified into **required-now**, **required-later**, or **not-in-scope**.
- [x] Every classified group has an explicit next action.
- [x] Every **required-now** group has ticket mapping, owner, and target sprint.
- [x] Marker budget enforcement uses canonical inventory exclusions only.
- [x] Weekly marker delta and top-hotspot owner assignment are required in tracker updates.
- [x] Marker trend gate: trend is stable/downward and no scope-critical must-fix marker is unowned.
- [x] Weekly publication includes scope-class open-item counts, marker WoW delta, top-10 hotspot ownership, and blockers with owner/date.
