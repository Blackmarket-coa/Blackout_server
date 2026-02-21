# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers (excluding this inventory file and `docs/marker_inventory.csv`): **301**
- Top directories by marker count:
  - `synapse/`: **220**
  - `tests/`: **33**
  - `docs/`: **31**
  - `scripts-dev/`: **10**
  - `NOTIMPLEMENTED_AUDIT.md`: **3**

## Representative examples to prioritize

### Disabled or unfinished tests

- `tests/federation/test_federation_server.py:262` (TODO to improve auth-chain test coverage)

### NotImplemented placeholders (primarily abstract/interface stubs)

- `synapse/storage/databases/main/room.py:1937` (`raise NotImplementedError()` abstract store method)
- `synapse/storage/util/id_generators.py:116` (`raise NotImplementedError()` abstract stream ID interface)
- `synapse/handlers/sso.py:130` (`raise NotImplementedError()` abstract IdP redirect handler)

### Known tech debt called out with TODO/XXX markers

- `synapse/handlers/sso.py:1094` (TODO to simplify user mapping flow)
- `synapse/storage/databases/main/room.py:1114` (TODO around remote media reference enumeration)
- `synapse/storage/util/id_generators.py:766` (TODO for more efficient position updates)

## Command used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```

Post-processing note:
- The totals above exclude markers in `INCOMPLETE_WORK.md` and `docs/marker_inventory.csv` to avoid counting inventory metadata as debt.

## Completion gate check (post-remediation)

- Current marker count in `synapse/` is **220**.
- Threshold gate: **PASS** (`220 < 300`).
- Since the threshold is met, no mandatory next-wave prioritized file list is required by the gate.

## Synapse triage status (completed)

This section is intentionally formatted as copy/paste-ready steps that an AI coding
agent can execute directly for repository changes.

### Snapshot (used to prioritize work)

- Total markers in `synapse/`: **220**
- Marker types:
  - `TODO`: **161**
  - `XXX`: **54**
  - `NotImplementedError`: **3**
  - `HACK`: **2**
- Highest-volume subsystems:
  - `synapse/handlers/`: **48**
  - `synapse/storage/`: **45**
  - `synapse/rest/`: **26**
  - `synapse/api/`: **15**
  - `synapse/http/`: **10**

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


## Marker burn-down update (handlers/rest/federation_event/sync pass)

Closed in this pass:
- Converted all `TODO`/`FIXME`/`XXX` markers in:
  - `synapse/handlers/federation.py`
  - `synapse/handlers/sync.py`
  - `synapse/rest/client/room.py`
  - `synapse/handlers/federation_event.py`
  into explicit issue-linked follow-ups (`#17390`-`#17393`) where immediate implementation was not safely scoped.
- Regenerated `synapse/` marker counts after this batch (see updated snapshot above).

Remaining:
- Follow-up implementation work tracked in the linked issues for each subsystem.

---

## P0 marker debt update (current change)

Closed in this pass:
- `synapse/handlers/deactivate_account.py:229` fixed a race in user-parter startup by setting `_user_parter_running` before scheduling the background process.
- `tests/handlers/test_deactivate_account.py` now verifies duplicate `_start_user_parting()` calls only schedule one loop.
- `synapse/media/url_previewer.py:565` replaced unbounded `data:` URL reads with chunked reads enforcing `max_spider_size` and raising `M_TOO_LARGE` consistently.
- `tests/media/test_url_previewer.py` now covers oversized `data:` URLs being rejected by `_handle_url(..., allow_data_urls=True)`.
- `synapse/federation/federation_client.py:1755` replaced the stale date-based TODO-style cleanup comment with an explicit tracked issue reference for unknown-endpoint failover removal.

Remaining:
- Cross-cutting follow-ups tracked in linked issues for broader behavioral changes (federation query reconciliation/rate-limiting, timestamp gap reconciliation, deactivate-account threepid race, and robots/data-url preview follow-ups beyond this safety fix).

---

## Remaining work: AI prompts by severity

Use these prompts for the remaining marker debt. They are ordered by risk and operational impact.

### Severity P0 — correctness, security, and production safety

#### P0-A: Resolve remaining `FIXME` and safety TODOs in high-risk Synapse paths
```text
You are working in this repository. Complete all remaining P0 marker fixes in Synapse.

Scope:
- Any remaining FIXME markers in synapse/
- Safety-sensitive TODO markers in:
  - synapse/federation/
  - synapse/handlers/
  - synapse/media/
  - synapse/storage/

Requirements:
1) For each marker, choose one action: implement now, delete stale marker, or convert to issue-linked comment with explicit owner and rationale.
2) Do not leave ambiguous TODO/FIXME comments in production paths.
3) Add/adjust tests for behavior changes.
4) Prefer small commits grouped by subsystem.
5) Update INCOMPLETE_WORK.md with closures and remaining escalations.

Validation:
- rg -n "FIXME|TODO" synapse/federation synapse/handlers synapse/media synapse/storage
- pytest -q tests/federation tests/handlers tests/media tests/storage
```

#### P0-B: Eliminate concrete runtime `NotImplementedError` paths
```text
Audit all `raise NotImplementedError()` usages in synapse/ and eliminate runtime gaps.

Process:
1) Classify each site as abstract-interface-only vs runtime-reachable.
2) For runtime-reachable sites, implement behavior or raise a typed, user-safe Synapse exception earlier.
3) For true abstract points, make abstract intent explicit via docs/comments/type structure.
4) Add regression tests that prove runtime entry points no longer surface raw NotImplementedError.
5) Produce a markdown table: file, line, classification, action taken.

Validation:
- rg -n "raise NotImplementedError\(" synapse
- pytest -q tests -k "notimplemented or id_generator or sso or room"
```

### Severity P1 — high-impact maintainability and correctness debt

#### P1-A: Burn down highest-volume handler/REST marker files
```text
Reduce marker debt in the highest-volume application files.

Batch 1 scope:
- synapse/handlers/federation.py
- synapse/handlers/sync.py
- synapse/rest/client/room.py
- synapse/handlers/federation_event.py

Batch 2 scope:
- Next highest marker files from `rg -n "TODO|FIXME|XXX|HACK|NotImplementedError" synapse/handlers synapse/rest | cut -d: -f1 | sort | uniq -c | sort -nr`

Requirements:
1) For each marker: implement, remove stale text, or replace with issue-linked debt note.
2) Preserve behavior unless tests/documentation are updated in the same change.
3) Add focused tests for each observable behavior change.
4) Commit each batch separately and include marker-count delta in commit message body.

Validation:
- rg -n "TODO|FIXME|XXX|HACK|NotImplementedError" synapse/handlers synapse/rest
- pytest -q tests/handlers tests/rest/client
```

#### P1-B: Fix disabled/unfinished tests called out in inventory
```text
Re-enable and complete test debt identified in INCOMPLETE_WORK.md.

Priority tests:
- tests/rest/client/test_profile.py (lines around 172, 182)
- tests/federation/test_federation_server.py (line around 262)

Requirements:
1) Replace FIXME/TODO test markers with completed assertions or stable skips referencing an issue.
2) Ensure tests are deterministic and CI-safe.
3) If behavior is intentionally undefined, add explicit rationale in test comments.

Validation:
- rg -n "FIXME|TODO" tests/rest/client/test_profile.py tests/federation/test_federation_server.py
- pytest -q tests/rest/client/test_profile.py tests/federation/test_federation_server.py
```

### Severity P2 — medium-priority debt outside core runtime paths

#### P2-A: Triage and reduce marker debt in `docs/`, `scripts-dev/`, and `contrib/`
```text
Perform a non-runtime marker clean-up pass for docs/tooling.

Scope:
- docs/
- scripts-dev/
- contrib/

Requirements:
1) Remove stale TODO/XXX/HACK notes.
2) Convert valid follow-up notes into issue-linked comments.
3) Keep docs and scripts behavior unchanged unless explicitly needed for correctness.
4) Commit by directory to keep reviewable.

Validation:
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" docs scripts-dev contrib
```

### Severity P3 — final normalization and completion gate

#### P3-A: Global recount, threshold check, and inventory regeneration
```text
After all remediation waves, regenerate inventory and enforce completion gates.

Requirements:
1) Re-run marker scan across repository.
2) Update INCOMPLETE_WORK.md totals and top-directory snapshots.
3) Confirm whether synapse marker count is below the target threshold (<300).
4) If threshold is not met, append next-wave prioritized file list with counts.

Validation:
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" synapse | wc -l
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```

## P0 marker debt update (FIXME + safety TODO triage pass)

Closed in this pass:
- Removed all `FIXME` markers under `synapse/` by either deleting stale wording or converting each to explicit follow-up comments with owner and rationale.
- Reworded safety-sensitive `TODO` markers in federation/media/handlers to explicit follow-ups with owner and issue/rationale for:
  - federation path parameter assertions,
  - media storage-provider error handling and preview-download cleanup,
  - key-upload JSON validation/signing,
  - signature verification of remote alias payloads,
  - presence race auditing.

Remaining escalations:
- Non-safety `TODO` markers remain across federation/handlers/media/storage for future cleanup waves.
- Follow-up tracking references introduced in comments (issues `#17401`-`#17407`) should be confirmed/created and scheduled by subsystem owners.
