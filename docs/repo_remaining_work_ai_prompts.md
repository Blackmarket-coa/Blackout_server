# Repository remaining-work backlog + AI prompt pack

_Date: 2026-02-28_

This document captures the remaining work in-repo and provides executable AI
prompts to close it in bounded waves.

## 1) Snapshot of work left (current branch)

### 1.1 Project completion tracker open items

Open checklist items (scope-labeled) in `docs/project_completion_tracker.md`:

- [required-now] Define canonical scope boundary linkage for all tracker items.
- [required-now] Re-validate all open tracker bullets against scope.
- [required-now] Ensure remaining open items have owner/due/exit/evidence.
- [required-now] Backlog necessity triage for blackout backend tracker.
- [required-later] Confirm generated reporting artifact merge policy.
- [required-later] Marker debt compliance gate.
- [required-later] Publish weekly scope-class open-item counts.
- [required-later] Publish weekly marker delta + hotspot ownership updates.
- [required-later] Publish blockers + owner + next action date.

### 1.2 Blackout backend tracker open-item map

Open item counts by section in `docs/development/blackout_backend_plan_tracker.md`:

| Open count | Section |
|---:|---|
| 6 | `0) Program Goals (North Star)` |
| 11 | `1) Remove Message Storage` |
| 8 | `2) Add signaling-only event type: m.blackout.signal` |
| 7 | `3) TURN/STUN service integration` |
| 7 | `4) Ephemeral retention (24–72h)` |
| 11 | `5) Security model alignment` |
| 7 | `6) Phone-as-server viability gates` |
| 4 | `7) Scalability strategy` |
| 4 | `Phase 1 — Signaling foundation` |
| 4 | `Phase 2 — Replication primitives` |
| 4 | `Phase 3 — File swarm` |
| 4 | `Phase 4 — Scale hardening` |
| 4 | `9) Existing code marker alignment map (initial seed)` |
| 5 | `10) Decisions needed now (blockers)` |
| 6 | `12) Strategic outcome checkpoint` |
| **93** | **Total open checklist items** |

### 1.3 Debt/risk status

- Marker budget gate: **PASS** (`current=110`, `budget=503`).
- Current marker scan total (excluding inventory artifacts): **117**.
- Raw request-serving runtime `raise N.I.E.(` in `synapse/`: **0 matches**.

## 2) Why completion is still blocked

Blocking conditions remain because:

1. Open `required-now` tracker items still exist in
   `docs/project_completion_tracker.md`.
2. Blackout backend tracker still contains a large open backlog (93 unchecked
   items) requiring explicit triage/closure sequencing.
3. Marker trend reconciliation is pending (`INCOMPLETE_WORK.md` latest published
   snapshot needs periodic refresh against current scan totals).

## 3) AI prompt pack for remaining work

Run prompts in order.

---

### Prompt A — Close open required-now tracker items

```text
You are working in this repository. Close all open required-now items in docs/project_completion_tracker.md.

Tasks:
1) For each open [required-now] item, do one of:
   - mark complete with in-repo evidence, or
   - mark deferred-with-signoff with approver/date/rationale/re-evaluation trigger.
2) Ensure each remaining open item still has owner/due/exit/evidence metadata.
3) Update the required-now execution metadata table status column to match item state.
4) Update docs/project_completion_closure_report.md gate status based on the new tracker state.

Validation:
- `rg -n "^- \[ \] \[required-now\]" docs/project_completion_tracker.md` returns no lines.
- `rg -n "Deferred-with-signoff|Complete" docs/project_completion_tracker.md` shows explicit status values for all required-now rows.

Commit message prefix: "tracker: close required-now completion blockers"
```

---

### Prompt B — Triage blackout backend backlog into executable phases

```text
You are working in this repository. Triage and operationalize open items in docs/development/blackout_backend_plan_tracker.md.

Tasks:
1) For each currently open checklist item, assign one scope class:
   - required-now
   - required-later
   - not-in-scope
2) For required-now items, add owner + target sprint/date + measurable exit criteria + evidence path.
3) Group required-now items into 3 implementation waves with objective deliverables.
4) Mark items as deferred-with-signoff only when justified and include full signoff metadata.

Validation:
- Every open item has a scope class.
- Every required-now item has owner/date/exit/evidence.
- A compact wave table exists mapping item -> wave -> owner -> due.

Commit message prefix: "tracker: operationalize blackout backend remaining backlog"
```

---

### Prompt C — Reconcile marker inventory and trend reporting

```text
You are working in this repository. Refresh INCOMPLETE_WORK.md and weekly reporting artifacts so marker trend status is auditable.

Tasks:
1) Recompute marker totals excluding inventory artifacts.
2) Update INCOMPLETE_WORK.md high-level totals and top-hotspot snapshot.
3) Generate a first filled weekly report using docs/weekly_completion_reporting_template.md.
4) Link the produced weekly report from docs/project_completion_tracker.md.

Validation:
- `python scripts-dev/check_marker_budget.py` passes.
- `rg -n "[T]ODO|[F]IXME|[T]BD|[X]XX|[H]ACK|[N]otImplementedError|[T]ODO_test_" . -g '!INCOMPLETE_WORK.md' -g '!docs/marker_inventory.csv' | wc -l` value matches the updated report snapshot.
- Weekly report includes scope-class counts, marker delta, top-10 hotspot ownership, and blockers.

Commit message prefix: "docs: publish weekly completion baseline report"
```

---

### Prompt E — Build upstream feature parity matrix (U1-U12)

```text
You are working in this repository. Build and maintain upstream parity tracking for features defined in docs/upstream_blackout_feature_build_plan.md.

Tasks:
1) Create/update docs/development/blackout_upstream_feature_matrix.md with U1-U12 support status (unsupported/partial/complete).
2) Add owner/due/exit/evidence fields for each unsupported or partial feature.
3) Cross-link the matrix from docs/project_completion_tracker.md.

Validation:
- rg -n "U1|U12|unsupported|partial|complete" docs/development/blackout_upstream_feature_matrix.md
- rg -n "blackout_upstream_feature_matrix|upstream_blackout_feature_build_plan" docs/project_completion_tracker.md

Commit message prefix: "tracker: maintain upstream feature parity matrix"
```

---

### Prompt D — Final completion gate rerun

```text
You are working in this repository. Re-run final completion gate and update docs/project_completion_closure_report.md.

Tasks:
1) Verify open required-now items are zero or deferred-with-signoff.
2) Verify marker budget passes and trend is non-increasing from last published week.
3) Verify runtime-path raw N.I.E. risk remains zero in request-serving flows.
4) Update closure report checklist statuses and recommendation.

Validation commands:
- python scripts-dev/check_marker_budget.py
- rg -n "^- \[ \] \[required-now\]" docs/project_completion_tracker.md
- rg -n "raise [N]otImplementedError\(" synapse

Commit message prefix: "docs: refresh completion closure gate"
```

## 4) Operator command bundle (copy/paste)

```bash
# A) open required-now items in completion tracker
rg -n "^- \[ \] \[required-now\]" docs/project_completion_tracker.md

# B) all open items in blackout backend tracker
rg -n "^- \[ \]" docs/development/blackout_backend_plan_tracker.md

# C) marker budget + current marker total
python scripts-dev/check_marker_budget.py
rg -n "[T]ODO|[F]IXME|[T]BD|[X]XX|[H]ACK|[N]otImplementedError|[T]ODO_test_" . -g '!INCOMPLETE_WORK.md' -g '!docs/marker_inventory.csv' | wc -l

# D) runtime-path raw N.I.E. check
rg -n "raise [N]otImplementedError\(" synapse
```
