# Repository remaining work — AI prompt pack (complete coverage)

_Date: 2026-03-14_

This prompt pack is the **single operator-ready catalog** for all currently open
checklist work left in this repository.

## 1) What is still open (repo snapshot)

The following command was used to locate open checklist items:

```bash
rg -n "^- \[ \]" docs INCOMPLETE_WORK.md
```

Open-item counts by file:

| File | Open items |
|---|---:|
| `docs/development/blackout_backend_plan_tracker.md` | 93 |
| `docs/distributed_self_healing_blueprint.md` | 33 |
| `docs/incident_response_maturity.md` | 6 |
| `docs/project_completion_tracker.md` | 5 |
| `INCOMPLETE_WORK.md` | 4 |
| `docs/development/blackout_weekly_tracker_update_template.md` | 4 |
| `docs/signaling_only_persistence_policy.md` | 1 |
| `docs/marker_budget_policy.md` | 1 |
| **Total** | **147** |

## 2) Execution order (strict)

1. **Governance prerequisites + signoff artifacts**
2. **Core completion tracker + inventory integrity**
3. **Blackout backend tracker operationalization (largest backlog)**
4. **Reliability + self-healing closure items**
5. **Incident maturity + weekly reporting operationalization**
6. **Final repo-wide closure verification**

---

## 3) AI prompts for *all* remaining work

### Prompt R1 — Close governance signoff stragglers

```text
You are working in this repository. Close the remaining signoff checklist items in governance/policy docs.

Target files:
- docs/signaling_only_persistence_policy.md
- docs/marker_budget_policy.md

Tasks:
1) Replace unchecked signoff bullets with completed records OR deferred-with-signoff entries.
2) Add explicit approver role, date, and evidence link for each signoff.
3) Keep policy intent unchanged; only harden auditability.
4) Cross-link signoff evidence from docs/project_completion_tracker.md if needed.

Validation:
- rg -n "^- \[ \]" docs/signaling_only_persistence_policy.md docs/marker_budget_policy.md returns zero lines.
- rg -n "Signed by|Sign-off|Approved|Evidence" docs/signaling_only_persistence_policy.md docs/marker_budget_policy.md shows explicit metadata.

Commit message prefix: "docs: finalize governance signoff records"
```

### Prompt R2 — Resolve remaining completion-tracker open items

```text
You are working in this repository. Close all remaining open items in docs/project_completion_tracker.md.

Tasks:
1) For each open [required-later] item, either:
   - complete with evidence already present in-repo, or
   - defer-with-signoff including owner, rationale, and re-evaluation date.
2) Ensure metadata table status aligns with checklist state.
3) Update the weekly reporting section links if new reports are added.
4) Keep scope labels aligned with docs/scope_boundary.md.

Validation:
- rg -n "^- \[ \]" docs/project_completion_tracker.md returns zero lines.
- rg -n "required-later|deferred-with-signoff|evidence|owner|due" docs/project_completion_tracker.md confirms metadata completeness.

Commit message prefix: "tracker: close remaining completion tracker items"
```

### Prompt R3 — Refresh incomplete-work inventory gate items

```text
You are working in this repository. Close checklist gates in INCOMPLETE_WORK.md with up-to-date evidence.

Tasks:
1) Re-run marker inventory with canonical exclusions.
2) Re-run runtime NotImplementedError risk scan for synapse request-serving code paths.
3) Update INCOMPLETE_WORK.md checklist to checked/unchecked based on real outputs.
4) If an item cannot be closed, add owner/date/next action in-place.

Validation commands:
- rg -n "[T]ODO|[F]IXME|[T]BD|[X]XX|[H]ACK|[N]otImplementedError|[T]ODO_test_" . -g '!INCOMPLETE_WORK.md' -g '!docs/marker_inventory.csv' | wc -l
- rg -n "raise [N]otImplementedError\(" synapse
- python scripts-dev/check_marker_budget.py

Commit message prefix: "docs: refresh incomplete-work closure gates"
```

### Prompt R4 — Operationalize blackout backend tracker (93 open items)

```text
You are working in this repository. Convert docs/development/blackout_backend_plan_tracker.md from backlog form to executable delivery waves.

Tasks:
1) For every currently open checklist item, add one explicit class:
   - required-now
   - required-later
   - not-in-scope
   - deferred-with-signoff
2) For each required-now item, add owner, due date, measurable exit criteria, and evidence path.
3) Group required-now work into Wave 1/2/3 with dependencies and blast-radius notes.
4) Add a compact status table: item -> class -> owner -> due -> status -> evidence.
5) Preserve protocol-compliance and feature-flag guardrails already documented elsewhere.

Validation:
- rg -n "^- \[ \]" docs/development/blackout_backend_plan_tracker.md still shows open items but each now includes class/owner/evidence metadata.
- rg -n "required-now|required-later|not-in-scope|deferred-with-signoff" docs/development/blackout_backend_plan_tracker.md
- rg -n "owner|due|exit criteria|evidence" docs/development/blackout_backend_plan_tracker.md

Commit message prefix: "tracker: operationalize blackout backend remaining backlog"
```

### Prompt R5 — Close self-healing blueprint acceptance gaps

```text
You are working in this repository. Close the remaining open checklist items in docs/distributed_self_healing_blueprint.md.

Tasks:
1) Split remaining items into:
   - implement-now (can be evidenced in-repo),
   - deferred-with-signoff (strategic or infra-dependent).
2) For implement-now items, add evidence links to tests/docs/runbooks.
3) For deferred items, add owner + target date + approval + trigger for re-evaluation.
4) Keep architecture recommendations intact; improve execution traceability.

Validation:
- rg -n "^- \[ \]" docs/distributed_self_healing_blueprint.md returns only intentionally deferred items with signoff metadata.
- rg -n "Evidence|Owner|Due|Deferred-with-signoff|Trigger" docs/distributed_self_healing_blueprint.md

Commit message prefix: "docs: reconcile self-healing blueprint open items"
```

### Prompt R6 — Complete incident-response maturity checklist

```text
You are working in this repository. Complete docs/incident_response_maturity.md remaining checklist items.

Tasks:
1) Add concrete references/templates for impact timeline, root cause, detection improvement, prevention action, runbook updates, and learning distribution.
2) Mark checklist items complete only when linked evidence exists.
3) If evidence is missing, leave item open but add owner + due + next action.

Validation:
- rg -n "^- \[ \]" docs/incident_response_maturity.md
- rg -n "impact|root cause|detection|prevention|runbook|learning" docs/incident_response_maturity.md

Commit message prefix: "docs: close incident response maturity checklist"
```

### Prompt R7 — Turn weekly tracker template into generated weekly output

```text
You are working in this repository. Convert docs/development/blackout_weekly_tracker_update_template.md checklist into an operational reporting workflow.

Tasks:
1) Produce a new dated weekly report in docs/reports/ using the template.
2) Ensure report contains:
   - marker budget enforcement status,
   - marker delta opened/closed/net,
   - top-hotspot DRI updates,
   - blockers with owner + next action date.
3) Update docs/project_completion_tracker.md to link the new report.
4) Mark template checklist items complete where the workflow is now evidenced.

Validation:
- rg -n "^- \[ \]" docs/development/blackout_weekly_tracker_update_template.md
- rg -n "marker budget|opened|closed|net|hotspot|blocker" docs/reports/weekly_completion_report_*.md

Commit message prefix: "docs: operationalize blackout weekly tracker reporting"
```

### Prompt R8 — Final repo-wide closure gate

```text
You are working in this repository. Run a final repo-wide remaining-work gate and publish closure status.

Tasks:
1) Re-scan all open checklist items across docs + INCOMPLETE_WORK.md.
2) Publish a closure snapshot in docs/project_completion_closure_report.md:
   - remaining open item count by file,
   - what is complete,
   - what is deferred-with-signoff,
   - go/no-go recommendation.
3) Ensure all deferred items have owner/date/approval/trigger metadata.

Validation commands:
- rg -n "^- \[ \]" docs INCOMPLETE_WORK.md
- python scripts-dev/check_marker_budget.py
- rg -n "Deferred-with-signoff|owner|due|approval|trigger" docs/project_completion_closure_report.md

Commit message prefix: "docs: publish repo-wide remaining work closure gate"
```

---

## 4) Operator command bundle

```bash
# 1) global open-checklist scan
rg -n "^- \[ \]" docs INCOMPLETE_WORK.md

# 2) marker budget + marker inventory
python scripts-dev/check_marker_budget.py
rg -n "[T]ODO|[F]IXME|[T]BD|[X]XX|[H]ACK|[N]otImplementedError|[T]ODO_test_" . -g '!INCOMPLETE_WORK.md' -g '!docs/marker_inventory.csv' | wc -l

# 3) runtime raw NotImplementedError sanity check
rg -n "raise [N]otImplementedError\(" synapse

# 4) highest-backlog tracker open items
rg -n "^- \[ \]" docs/development/blackout_backend_plan_tracker.md
```

## 5) Definition of completion for this prompt pack

This pack is considered complete when:

1. Every file currently containing unchecked checklist items has at least one dedicated prompt above.
2. Prompt sequence R1→R8 can be executed independently in small PR waves.
3. Each prompt includes explicit validation commands and commit prefix guidance.
