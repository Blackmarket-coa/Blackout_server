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

- Potential incomplete-work markers: **496** (excluding the inventory file itself).
- Marker concentration:
  - `synapse/`: 420
  - `tests/`: 37
  - `docs/`: 15
  - `contrib/`: 12
  - `scripts-dev/`: 8

### Initial risk interpretation

- **High**: Core code marker concentration in `synapse/`.
- **Medium**: Test/doc/contrib cleanup debt.
- **High**: Any production-path `NotImplementedError` handling gaps.

## 3) Workstreams and status board

Legend: `[ ]` not started, `[-]` in progress, `[x]` done.

### A. Code and test debt reduction

- [ ] A1. Re-run marker inventory and publish weekly delta.
- [ ] A2. Classify each marker: `intentional`, `defer`, `must-fix`.
- [ ] A3. Resolve all `must-fix` markers in production paths.
- [ ] A4. Resolve outdated TODO/FIXME in tests and docs.
- [ ] A5. Establish and enforce a maximum marker budget for new changes.

### B. Runtime correctness and unimplemented branches

- [ ] B1. Audit all `NotImplementedError` occurrences.
- [ ] B2. Tag each as `abstract-interface-ok` or `runtime-path-risk`.
- [ ] B3. Eliminate/replace all `runtime-path-risk` occurrences.
- [ ] B4. Add regression tests for each resolved runtime-path-risk branch.

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

## 6) Ownership template

Populate and keep current:

- Code debt owner: _TBD_
- Runtime correctness owner: _TBD_
- SRE/HA owner: _TBD_
- Data durability owner: _TBD_
- Incident/process owner: _TBD_

## 7) Review cadence

- Weekly: update metrics and board statuses.
- Bi-weekly: triage marker backlog and adjust budget.
- Monthly: SLO review and risk re-ranking.
- Quarterly: restore/failover drills and checklist recertification.
