# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers (excluding this inventory file and `docs/marker_inventory.csv`): **495**
- Top directories by marker count:
  - `synapse/`: **409**
  - `tests/`: **32**
  - `docs/`: **29**
  - `contrib/`: **12**
  - `scripts-dev/`: **9**

## Representative examples to prioritize

### Disabled or unfinished tests

- `tests/rest/client/test_profile.py:172` (FIXME around profile display name behavior)
- `tests/rest/client/test_profile.py:182` (FIXME around profile avatar URL behavior)
- `tests/federation/test_federation_server.py:262` (TODO to improve auth-chain test coverage)

### NotImplemented placeholders (primarily abstract/interface stubs)

- `synapse/storage/databases/main/room.py:1937` (`raise NotImplementedError()` abstract store method)
- `synapse/storage/util/id_generators.py:116` (`raise NotImplementedError()` abstract stream ID interface)
- `synapse/handlers/sso.py:130` (`raise NotImplementedError()` abstract IdP redirect handler)

### Known tech debt called out with FIXMEs

- `synapse/handlers/deactivate_account.py:91` (race condition note)
- `synapse/federation/federation_client.py:1277` (signature failure handling)
- `synapse/media/url_previewer.py:481` (error passthrough behavior)

## Command used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```

## Synapse triage status (completed)

This section is intentionally formatted as copy/paste-ready steps that an AI coding
agent can execute directly for repository changes.

### Snapshot (used to prioritize work)

- Total markers in `synapse/`: **409**
- Marker types:
  - `TODO`: **235**
  - `NotImplementedError`: **67**
  - `XXX`: **63**
  - `FIXME`: **43**
  - `HACK`: **2**
- Highest-volume subsystems:
  - `synapse/handlers/`: **140**
  - `synapse/storage/`: **71**
  - `synapse/rest/`: **39**
  - `synapse/federation/`: **31**
  - `synapse/media/`: **20**

---

## Copy/paste task 1: P0 correctness and safety fixes

### Goal
Reduce high-risk debt first by resolving `FIXME` and safety-critical TODOs in
federation/media/account paths.

### Scope
- Start with:
  - `synapse/handlers/deactivate_account.py`
  - `synapse/federation/federation_client.py`
  - `synapse/media/url_previewer.py`

### AI prompt (copy/paste)
```text
You are working in this repository. Implement P0 correctness/safety fixes for TODO/FIXME markers in:
- synapse/handlers/deactivate_account.py
- synapse/federation/federation_client.py
- synapse/media/url_previewer.py

Requirements:
1) Replace marker comments with concrete code changes where feasible.
2) If a marker cannot be fully implemented safely, convert it into an explicit tracked issue reference in code comments.
3) Add or update tests for each behavior change.
4) Run only relevant test targets first, then broader targets if fast.
5) Commit with message prefix: "synapse: resolve p0 marker debt".
6) Update INCOMPLETE_WORK.md with what was closed and what remains.
```

### Verification commands (copy/paste)
```bash
rg -n "FIXME|TODO" synapse/handlers/deactivate_account.py synapse/federation/federation_client.py synapse/media/url_previewer.py
pytest -q tests/federation tests/media tests/handlers -k "deactivate or federation or preview"
```

---

## Copy/paste task 2: Runtime NotImplementedError elimination

### Goal
Remove concrete runtime `NotImplementedError` paths in Synapse code that are not
true abstract extension points.

### Priority files
- `synapse/storage/util/id_generators.py`
- `synapse/storage/databases/main/room.py`
- `synapse/handlers/sso.py`

### AI prompt (copy/paste)
```text
Audit synapse/ for raise NotImplementedError() and classify each instance as:
A) valid abstract interface, or
B) concrete runtime gap.

For category B:
1) Implement the missing behavior or fail earlier with a typed, user-safe error.
2) Add tests proving runtime paths no longer raise raw NotImplementedError.
3) Keep category A sites but make abstract intent explicit with comments/type structure.
4) Produce a short markdown report with file-by-file disposition.
5) Commit with message prefix: "synapse: remove runtime notimplemented paths".
```

### Verification commands (copy/paste)
```bash
rg -n "raise NotImplementedError\(" synapse
pytest -q tests -k "id_generator or room or sso"
```

---

## Copy/paste task 3: High-volume handler/REST marker burn-down

### Goal
Reduce marker count in highest-volume files while preserving behavior and test
coverage.

### Priority files (batch 1)
- `synapse/handlers/federation.py` (18)
- `synapse/handlers/sync.py` (15)
- `synapse/rest/client/room.py` (12)
- `synapse/handlers/federation_event.py` (12)

### AI prompt (copy/paste)
```text
Perform a marker burn-down pass on the following files:
- synapse/handlers/federation.py
- synapse/handlers/sync.py
- synapse/rest/client/room.py
- synapse/handlers/federation_event.py

Process:
1) For each TODO/XXX/FIXME: implement, delete stale note, or convert to issue-linked comment.
2) Keep patches small and behavior-focused; split commits by subsystem.
3) Add tests for any changed observable behavior.
4) After each commit, rerun targeted tests for touched modules.
5) Update INCOMPLETE_WORK.md marker counts after batch completion.
```

### Verification commands (copy/paste)
```bash
rg -n "TODO|FIXME|XXX|HACK|NotImplementedError" synapse/handlers/federation.py synapse/handlers/sync.py synapse/rest/client/room.py synapse/handlers/federation_event.py
pytest -q tests/handlers tests/rest/client -k "federation or sync or room"
```

---

## Completion gate for “Synapse complete”

Use this exact checklist:

- [ ] All P0 items are either fixed in code with tests or linked to tracked issues with owners.
- [ ] No concrete runtime path in `synapse/` raises raw `NotImplementedError`.
- [ ] Marker count in `synapse/` is below **300** after first remediation wave.
- [ ] Marker inventory is regenerated and committed.

### Recount command (copy/paste)
```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" synapse | wc -l
```

### Regeneration command (copy/paste)
```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```
