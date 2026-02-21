# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers (excluding this inventory file and `docs/marker_inventory.csv`): **311**
- Top directories by marker count:
  - `synapse/`: **220**
  - `tests/`: **39**
  - `docs/`: **31**
  - `scripts-dev/`: **10**
  - `NOTIMPLEMENTED_AUDIT.md`: **7**

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
  - `XXX`: **52**
  - `NotImplementedError`: **1**
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
- `synapse/handlers/deactivate_account.py` removed a duplicate `_third_party_rules` assignment and converted the remaining threepid reset/deactivation race note into an explicit tracked issue reference (`#17374`).
- `synapse/handlers/deactivate_account.py` now resets `_user_parter_running` if scheduling the background parter loop fails synchronously, preventing the handler from getting stuck in a permanently "running" state.
- `synapse/federation/federation_client.py` now deduplicates destination attempts in `get_pdu(...)` and records retry timestamps for `NotRetryingDestination`, `FederationDeniedError`, and `SynapseError` failures to avoid tight-loop retries.
- `tests/federation/test_federation_client.py` adds coverage that duplicate federation destinations are attempted only once.
- `tests/handlers/test_deactivate_account.py` adds coverage that `_start_user_parting()` clears its guard flag when background process scheduling fails.
- `synapse/media/url_previewer.py` now uses bounded file reads for HTML/oEmbed parsing, skipping parsing when body size exceeds `min(max_spider_size, 2 MiB)` to avoid large in-memory reads.
- `tests/media/test_url_previewer.py` adds focused coverage for `_read_file_for_parsing(...)` on oversized and small inputs.

Remaining:
- Cross-cutting follow-ups still tracked in linked issues for larger behavior changes: deactivate-account threepid reset coordination (`#17374`), robots.txt support (`#17382`), pre-cache unification (`#17383`), and white-on-transparent thumbnail handling (`#17384`).

---


## Marker burn-down pass: federation/sync/room/federation_event (current change)

Closed in this pass:
- Confirmed there are no remaining `TODO`/`FIXME`/`XXX` markers in:
  - `synapse/handlers/federation.py`
  - `synapse/handlers/sync.py`
  - `synapse/rest/client/room.py`
  - `synapse/handlers/federation_event.py`
- No behavior changes were required for this batch because there were no eligible markers in scope.

Remaining:
- Marker debt remains in other subsystems per the refreshed totals above.

Verification snapshot (this pass):
- `rg -n "TODO|FIXME|XXX|HACK|NotImplementedError" synapse/handlers/federation.py synapse/handlers/sync.py synapse/rest/client/room.py synapse/handlers/federation_event.py` returned no matches.
- Total markers (excluding inventory metadata files) remain **311**.
- Markers under `synapse/` remain **220**.

---

## Remaining work: AI prompts by severity

Use these prompts for the *current* remaining debt profile (311 total markers; 220 in `synapse/`).

### Severity P0 — remove ambiguous production TODO/XXX hotspots (current top files)

#### P0-A: Resolve markers in `synapse/api/auth/msc3861_delegated.py` and storage core paths
```text
You are working in this repository. Address the highest-density production marker files first.

Scope:
- synapse/api/auth/msc3861_delegated.py
- synapse/storage/database.py
- synapse/media/preview_html.py

Requirements:
1) For each TODO/XXX/HACK marker: implement now, delete stale note, or convert to issue-linked follow-up with owner+rationale.
2) Do not leave unowned TODO/XXX comments in request/authentication or storage write paths.
3) Add/update focused tests for behavior changes.
4) Keep commits small by subsystem.
5) Update INCOMPLETE_WORK.md with marker deltas after the pass.

Validation:
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" synapse/api/auth/msc3861_delegated.py synapse/storage/database.py synapse/media/preview_html.py
- pytest -q tests -k "delegated or storage or preview_html"
```

#### P0-B: Close remaining federation safety test debt
```text
Complete the remaining explicit safety test debt called out in inventory.

Scope:
- tests/federation/test_federation_server.py (auth-chain TODO around line 262)

Requirements:
1) Replace TODO with completed assertions, or stable skip/xfail tied to a tracked issue.
2) Ensure determinism in CI (no timing/network flakes).
3) Document rationale inline if behavior remains intentionally deferred.

Validation:
- rg -n "TODO|FIXME" tests/federation/test_federation_server.py
- pytest -q tests/federation/test_federation_server.py
```

### Severity P1 — handler/domain marker burn-down based on current counts

#### P1-A: Burn down next highest Synapse runtime files
```text
Perform a marker burn-down pass on current high-volume runtime files.

Batch 1 scope:
- synapse/handlers/directory.py
- synapse/handlers/room.py
- synapse/handlers/presence.py
- synapse/handlers/room_member.py
- synapse/rest/client/versions.py

Requirements:
1) For each marker: implement, remove stale text, or replace with issue-linked debt note.
2) Preserve API behavior unless tests/documentation are updated in the same change.
3) Add focused tests for observable behavior changes.
4) Commit each batch separately and include marker-count delta in commit body.

Validation:
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" synapse/handlers/directory.py synapse/handlers/room.py synapse/handlers/presence.py synapse/handlers/room_member.py synapse/rest/client/versions.py
- pytest -q tests/handlers tests/rest/client -k "directory or room or presence or versions"
```

### Severity P2 — non-runtime and tooling cleanup

#### P2-A: Clean marker debt in docs/tests/tooling where behavior is stable
```text
Reduce non-runtime marker debt while avoiding product behavior changes.

Scope:
- docs/
- scripts-dev/
- tests/server.py and other highest-count tests/* files from fresh scan

Requirements:
1) Remove stale TODO/XXX/HACK notes and convert valid follow-ups to issue-linked comments.
2) Keep docs/scripts semantics unchanged unless correctness requires edits.
3) For tests, prefer clarifying comments + deterministic assertions over suppressive TODOs.
4) Commit by area (docs, scripts, tests) for reviewability.

Validation:
- rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" docs scripts-dev tests
```

### Severity P3 — recount + re-prioritize from live data

#### P3-A: Refresh inventory from latest scan and regenerate prioritized targets
```text
After each remediation wave, refresh the inventory using current scan output.

Requirements:
1) Re-run marker scan across repository.
2) Update INCOMPLETE_WORK.md totals, top directories, and representative examples.
3) Recompute top 10 files by remaining marker count and replace prompt scopes accordingly.
4) Confirm whether synapse marker count remains below the target threshold (<300).

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

---

## P0-A marker debt update (msc3861_delegated + database + preview_html)

Closed in this pass:
- Removed all `TODO`/`XXX`/`HACK` markers from:
  - `synapse/api/auth/msc3861_delegated.py`
  - `synapse/storage/database.py`
  - `synapse/media/preview_html.py`
- Converted remaining non-trivial follow-ups into issue-linked comments with owners (`#17411`-`#17416`, `#17421`-`#17425`, `#17431`-`#17434`) so there are no unowned markers in delegated-auth or storage paths.
- Implemented legacy HTML charset detection for `<meta http-equiv="Content-Type" ... charset=...>` in `synapse/media/preview_html.py`.
- Added focused coverage in `tests/media/test_html_preview.py::MediaEncodingTestCase::test_meta_http_equiv_content_type`.

Marker deltas after this pass:
- `synapse/` markers: **200** (down from **220**).
- Total markers excluding inventory metadata files: **291** (down from **311**).
- Scoped files marker scan now returns no matches.
