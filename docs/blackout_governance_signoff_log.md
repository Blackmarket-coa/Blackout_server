# Blackout Governance Sign-off Log

> Status: **Template / Pending formal approvals**

This file is an auditable checklist for governance approvals. Entries must be backed by external approval records (ticket links, signed minutes, or change-control records).

| Date | Gate | Role | Owner | Decision | Evidence |
|---|---|---|---|---|---|
| TBD | Phase 0 Threat/Abuse Model Ratification | Security Lead | TBD | Pending | Link to signed review record |
| TBD | Phase 0 Schema + CI Drift Controls | Policy Lead | TBD | Pending | Link to CI run + approval record |
| TBD | Phase 0 Rollback + Incident Runbook Readiness | Operations Lead | TBD | Pending | Link to runbook review |
| TBD | Phase 1 Core Policy Rollout Entry | Federation Lead | TBD | Pending | Link to staging compatibility report |
| TBD | Phase 2 Pilot Enablement (cohort-only) | Security + Operations | TBD | Pending | Link to SLO guardrail approval |
| TBD | Phase 3 Broad Rollout | Security + Operations | TBD | Pending | Link to go/no-go record |

## Rollback Criteria References
- Delayed fanout and timing-jitter pilots must rollback automatically when latency/reliability SLO thresholds breach.
- Runbook references for rollback and incident handling:
  - `docs/blackout-ops-runbook.md`
  - `docs/blackout_delivery_execution_report.md`
