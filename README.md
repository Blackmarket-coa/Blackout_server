# Blackout Server

This repository contains the Blackout server workstream on top of Synapse, including scope/completion tracking and upstream parity planning artifacts.

## New features and updates

### 1) Upstream feature parity matrix (U1-U12)

A new canonical matrix tracks support status for upstream Blackout feature families (`unsupported`, `partial`, `complete`) with explicit owner, due date, measurable exit criteria, and evidence links.

- Matrix: `docs/development/blackout_upstream_feature_matrix.md`
- Source plan: `docs/upstream_blackout_feature_build_plan.md`
- Tracker cross-link: `docs/project_completion_tracker.md`

### 2) Weekly completion reporting baseline (2026-03-02)

A filled weekly completion report is published with:

- scope-class open-item counts,
- week-over-week marker delta,
- top-10 hotspot ownership,
- blockers with owners and next action dates,
- command sequence used for reproducibility.

Report artifact:
- `docs/reports/weekly_completion_report_2026-03-02.md`

### 3) Completion closure gate refresh

The final completion closure report has been refreshed with current gate checks and recommendation status, including:

- required-now open-item gate,
- marker budget gate,
- marker trend check,
- runtime raw `NotImplementedError` risk check,
- deployment-readiness recommendation.

Closure report:
- `docs/project_completion_closure_report.md`

### 4) Backend backlog triage operationalization

The blackout backend plan tracker now includes structured scope classification and implementation wave planning for open backlog items, including required-now ownership and due metadata.

Tracker artifact:
- `docs/development/blackout_backend_plan_tracker.md`

## Quick validation commands

```bash
python scripts-dev/check_marker_budget.py
rg -n "^- \[ \] \[required-now\]" docs/project_completion_tracker.md
rg -n "raise [N]otImplementedError\(" synapse
rg -n "U1|U12|unsupported|partial|complete" docs/development/blackout_upstream_feature_matrix.md
```
