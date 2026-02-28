# Tracker / marker audit report

Generated: **2026-02-28 20:43:03Z**

## Tracker checklist status

| Tracker | Checked | Unchecked | Total |
|---|---:|---:|---:|
| `docs/development/blackout_backend_plan_tracker.md` | 8 | 115 | 123 |
| `docs/development/blackout_weekly_tracker_update_template.md` | 0 | 4 | 4 |
| `docs/project_completion_tracker.md` | 57 | 5 | 62 |

## Incomplete-work markers

- Total markers (excluding generated inventory/report files): **40**

### By top-level path

- `docs/`: 21
- `NOTIMPLEMENTED_AUDIT.md/`: 12
- `docker/`: 2
- `synapse/`: 2
- `debian/`: 1
- `pylint.cfg/`: 1
- `tests/`: 1

### By keyword

- `NotImplementedError`: 37
- `TODO`: 7
- `FIXME`: 3
- `XXX`: 3
- `TBD`: 2
- `HACK`: 2
- `TODO_test_`: 2

### Top files by marker count

- `NOTIMPLEMENTED_AUDIT.md`: 12
- `docs/runtime_notimplemented_audit.md`: 10
- `docs/notimplemented_audit_report.md`: 6
- `docker/Dockerfile-dhvirtualenv`: 2
- `docs/marker_budget_policy.md`: 2
- `synapse/http/federation/srv_resolver.py`: 2
- `docs/project_completion_tracker.md`: 1
- `debian/build_virtualenv`: 1
- `docs/scope_alignment_evidence.md`: 1
- `docs/server_usability_validation.md`: 1
- `pylint.cfg`: 1
- `tests/util/test_check_dependencies.py`: 1

## Commands used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" . \
  -g "!docs/marker_inventory.csv" \
  -g "!INCOMPLETE_WORK.md" \
  -g "!docs/incomplete_work_line_by_line_fixes.md" \
  -g "!docs/tracker_todo_fixme_report.md"
```
