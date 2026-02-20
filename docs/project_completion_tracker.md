# Project completion tracker

This tracker combines:

- implementation debt signals from `INCOMPLETE_WORK.md`, and
- production resilience milestones from `docs/distributed_self_healing_blueprint.md`.

Use it as the single progress page for technical completion.

## 1) Completion definition

The project is considered complete when all of the following are true:

- Code-level incomplete-work markers are triaged and reduced to an agreed steady-state budget.
- No runtime-critical `NotImplementedError` branches remain unresolved.
- Reliability SLOs are defined, instrumented, and demonstrably met.
- HA/failover architecture is implemented and routinely tested.
- Backup/restore and incident runbooks are validated by recurring drills.

## 2) Baseline snapshot (starting point)

From the latest inventory scan:

- Potential incomplete-work markers: **505** (excluding the inventory file itself).
- Marker concentration:
  - `synapse/`: 415
  - `tests/`: 34
  - `docs/`: 32
  - `contrib/`: 12
  - `scripts-dev/`: 8

### Baseline refresh notes (2026-02-20)

- Marker inventory was re-run with the same regex used in `INCOMPLETE_WORK.md`.
- Delta vs prior snapshot is **-2** net markers (507 -> 505).
- `synapse/` marker count decreased (420 -> 415), while docs remain the largest non-code growth area.

### Initial risk interpretation

- **High**: Core code marker concentration in `synapse/`.
- **Medium**: Test/doc/contrib cleanup debt.
- **High**: Any production-path `NotImplementedError` handling gaps.

## 3) Workstreams and status board

Legend: `[ ]` not started, `[-]` in progress, `[x]` done.

### A. Code and test debt reduction

- [-] A1. Re-run marker inventory and publish weekly delta.
- [ ] A2. Classify each marker: `intentional`, `defer`, `must-fix`.
- [ ] A3. Resolve all `must-fix` markers in production paths.
- [ ] A4. Resolve outdated TODO/FIXME in tests and docs.
- [ ] A5. Establish and enforce a maximum marker budget for new changes.

### B. Runtime correctness and unimplemented branches

- [x] B1. Audit all `NotImplementedError` occurrences.
- [x] B2. Tag each as `abstract-interface-ok` or `runtime-path-risk`.
- [x] B3. Eliminate/replace all `runtime-path-risk` occurrences.
- [x] B4. Add regression tests for each resolved runtime-path-risk branch.

### C. Reliability/SLO implementation

- [ ] C1. Finalize SLOs (availability, federation recovery, RPO/RTO).
- [ ] C2. Add instrumentation to measure each SLO directly.
- [ ] C3. Define alert thresholds and paging policies.
- [ ] C4. Publish monthly SLO reports.

### D. HA architecture and self-healing controls

- [ ] D1. Worker topology deployed (generic, federation, background, persister).
- [ ] D2. Redis replication/cache coherence operational.
- [ ] D3. PostgreSQL HA with automated failover validated.
- [ ] D4. Reverse proxy/LB health routing validated.
- [ ] D5. Liveness/readiness checks on all critical services.
- [ ] D6. Automated rollback on bad deploy behavior verified.

### E. Data durability and disaster recovery

- [ ] E1. Daily full + incremental/WAL backups operational.
- [ ] E2. Automated backup verification pipeline implemented.
- [ ] E3. Quarterly restore drill passing.
- [ ] E4. Replication/lag/capacity alerting implemented.

### F. Operational maturity and incident readiness

- [ ] F1. Threat model scenarios mapped to detection + auto-response + runbook.
- [ ] F2. Runbooks exist for DNS outage, cert expiry, region loss, bad rollout.
- [ ] F3. Chaos drills executed (worker loss, node loss, DB primary fail).
- [ ] F4. Postmortem template/checklist adopted for all major incidents.

### G. 30/60/90 rollout alignment

- [ ] G1. Day 0-30 milestones complete.
- [ ] G2. Day 31-60 milestones complete.
- [ ] G3. Day 61-90 milestones complete.


### H. Decentralized encrypted federation refactor package

- [x] H1. Architectural diagram (text form) published and versioned.
- [x] H2. Target modular folder structure agreed (`core/`, `network/`, `crypto/`, `governance/`, `tasks/`, `ledger/`, `streaming/`, `compat/`).
- [x] H3. Refactor checklist items triaged into phased implementation backlog.
- [ ] H4. Event schema implemented with signed hash-linked envelope fields.
- [ ] H5. CRDT integration path selected (Yjs or Automerge) and prototype validated.
- [ ] H6. Encrypted message flow specification reviewed by security owner.
- [ ] H7. Node boot sequence implemented for snapshot + replay startup.
- [ ] H8. Recovery sequence implemented and tested for offline rejoin.
- [ ] H9. Performance optimization plan tracked against low-memory profile targets.
- [ ] H10. Security audit checklist incorporated into release readiness review.
- [ ] H11. Migration approach (`dual-write`, `shadow-read`, `canary`, `cutover`, `rollback`) tracked with owners and dates.
- [x] H12. README and operator docs point to the canonical refactor blueprint and tracker.

## 4) Milestone gates

### Gate 1 — Code health gate

Exit criteria:

- `must-fix` marker queue is empty.
- Runtime-path `NotImplementedError` risks are eliminated.
- Core regression suite green for touched domains.

### Gate 2 — Reliability gate

Exit criteria:

- SLO dashboards and alerts active.
- HA/failover controls validated in staging and production.
- Restore + failover drills completed in last quarter.

### Gate 3 — Resilience gate

Exit criteria:

- Federation backlog recovery target met after induced outage.
- No single point of failure in app/DB/cache/ingress.
- Operator onboarding/runbook pack published for community operators.

## 5) Metrics to track weekly

- Total marker count and change vs previous week.
- Marker count in `synapse/`.
- Count of runtime-path-risk `NotImplementedError` branches.
- SLO attainment by objective.
- Mean time to detect (MTTD) and recover (MTTR) from drills/incidents.
- Backup verification pass rate.

- Refactor package completion ratio (H-items done / total H-items).
- Recovery drill success rate for snapshot+replay rejoin scenarios.

## 6) Ownership template

Populate and keep current:

- Code debt owner: _TBD_
- Runtime correctness owner: _TBD_
- SRE/HA owner: _TBD_
- Data durability owner: _TBD_
- Incident/process owner: _TBD_
- Federation refactor owner: _TBD_
- Crypto/security owner: _TBD_
- Migration/cutover owner: _TBD_

## 7) Review cadence

- Weekly: update metrics and board statuses.
- Bi-weekly: triage marker backlog and adjust budget.
- Monthly: SLO review and risk re-ranking.
- Quarterly: restore/failover drills and checklist recertification.


### Runtime-path risk closure notes (2026-02-20)

- Runtime-path risks identified in the inventory were eliminated by replacing `NotImplementedError` branches in request handlers with explicit `SynapseError` responses in:
  - `synapse/handlers/sync.py`
  - `synapse/handlers/room.py`
  - `synapse/federation/federation_server.py`
- Added regression tests covering:
  - appservice-user `/sync` rejection path in sync handler logic
  - missing `event_id` rejection for federation `/state_ids` requests
  - invalid `/search` `order_by` rejection path (`M_INVALID_PARAM`)
  - non-presence-worker visibility check path now returns explicit `503` `SynapseError` (no `NotImplementedError`)
- Runtime-path-risk `NotImplementedError` count is now tracked at **0** for request-serving flows addressed by this tracker.


### Refactor package documentation closure notes (2026-02-20)

- H1 marked complete: text architecture diagram is published in
  `docs/distributed_self_healing_blueprint.md` under
  "Refactor package for decentralized encrypted federation" ->
  "1) Architectural diagram (text form)".
- H2 marked complete: target modular folder structure is defined in the same
  blueprint under "2) Target folder structure".
- H3 marked complete: refactor checklist is published as a triaged backlog in
  the blueprint under "3a) Phased implementation backlog (triaged)" for
  explicit phase sequencing and implementation tracking.
- H12 marked complete: top-level README and blackout operator runbook now both
  link operators to the canonical blueprint + project completion tracker pages.
