# Server usability validation

_Date: 2026-03-06_

This report captures a deployment-readiness usability validation pass using commands that are feasible in the current CI/container environment, plus explicit non-runnable checks with required runtime context.

## 1) Command log (pass/fail with evidence)

### 1.1 Environment/build sanity

| Status | Command | Result |
|---|---|---|
| PASS | `python -V` | `Python 3.10.19` |
| PASS | `cargo --version` | `cargo 1.92.0` |
| PASS | `rustc --version` | `rustc 1.92.0` |
| PASS | `pytest --version` | `pytest 9.0.2` |

### 1.2 Service startup + health endpoint checks

| Status | Command | Result |
|---|---|---|
| WARN (env limitation) | `python -m synapse.app.homeserver --help` | Failed: `importlib.metadata.PackageNotFoundError: blackout-server` (package metadata not installed in this container). |
| PASS | `rg -n "(/health|health endpoint|ready endpoint|liveness)" docs synapse` | Located health endpoint and references in `synapse/rest/health.py`, `synapse/app/homeserver.py`, `synapse/app/generic_worker.py`, and ops docs. |

Required runtime command set (non-runnable here, requires deployed server and config):

```bash
python -m synapse.app.homeserver --config-path homeserver.yaml
curl -sf http://127.0.0.1:8008/health
```

### 1.3 Core API smoke tests (auth / room create / join / send / read)

Status: **WARN (non-runnable in this environment)**

Reason: no running homeserver + no configured test users/registration secrets in this container.

Required commands in deployment-like env:

```bash
# health and versions
curl -sf http://127.0.0.1:8008/_matrix/client/versions

# register/login flow (depends on configured auth mode)
# example placeholder flow; adapt to deployment registration policy
curl -sS -XPOST http://127.0.0.1:8008/_matrix/client/v3/register -d '{"username":"smoke","password":"<secret>","auth":{"type":"m.login.dummy"}}'

# room lifecycle smoke (requires access token)
curl -sS -XPOST http://127.0.0.1:8008/_matrix/client/v3/createRoom -H "Authorization: Bearer $TOKEN" -d '{}'
curl -sS -XPOST http://127.0.0.1:8008/_matrix/client/v3/rooms/$ROOM_ID/join -H "Authorization: Bearer $TOKEN" -d '{}'
curl -sS -XPUT  http://127.0.0.1:8008/_matrix/client/v3/rooms/$ROOM_ID/send/m.room.message/$TXN -H "Authorization: Bearer $TOKEN" -d '{"msgtype":"m.text","body":"smoke"}'
curl -sS "http://127.0.0.1:8008/_matrix/client/v3/rooms/$ROOM_ID/messages?dir=b&limit=10" -H "Authorization: Bearer $TOKEN"
```

### 1.4 Federation-related smoke tests

| Status | Command | Result |
|---|---|---|
| WARN (env limitation) | `python scripts-dev/federation_client.py --help` | Failed: `ModuleNotFoundError: No module named 'srvlookup'`. |

Required environment and command:

```bash
pip install srvlookup
python scripts-dev/federation_client.py --server <origin> --destination <remote> --action ping
python scripts-dev/federation_client.py --server <origin> --destination <remote> --action smoke
```

### 1.5 Backup/restore verification command checks

| Status | Command | Result |
|---|---|---|
| PASS | `bash -n scripts-dev/blackout/backup_run.sh scripts-dev/blackout/backup_verify.sh scripts-dev/blackout/quarterly_restore_drill.sh` | Scripts are syntactically valid. |
| WARN (env limitation) | `command -v pg_basebackup` | Missing in container. |
| WARN (env limitation) | `command -v pg_verifybackup` | Missing in container. |
| WARN (env limitation) | `command -v pg_controldata` | Missing in container. |

Required runtime commands (host with PostgreSQL tooling + backup data):

```bash
BACKUP_ROOT=/var/backups/postgres scripts-dev/blackout/backup_run.sh
BACKUP_ROOT=/var/backups/postgres REPORT_DIR=/var/backups/postgres/verification-reports scripts-dev/blackout/backup_verify.sh
BACKUP_ROOT=/var/backups/postgres DRILL_ROOT=/var/tmp/postgres-restore-drill scripts-dev/blackout/quarterly_restore_drill.sh
```

### 1.6 Representative regression subset (touched subsystems)

| Status | Command | Result |
|---|---|---|
| PASS | `python tests/check_runtime_notimplemented.py` | `OK: no runtime raise NotImplementedError sites found under synapse/.` |
| WARN (env limitation) | `pytest -q blackout_runtime_tests/test_readiness.py blackout_runtime_tests/test_runtime.py` | Collection failed: `ModuleNotFoundError: blackout_runtime` (package/module not installed in current interpreter path). |

### 1.7 Requested validation rerun (2026-03-06 follow-up)

| Status | Command | Result |
|---|---|---|
| PASS | `python -V` | `Python 3.10.19` |
| PASS | `cargo --version` | `cargo 1.92.0` |
| WARN (env limitation) | `pytest -q tests -k "federation or media or handlers"` | Collection failed across suite (`273 errors`) due to missing installed package metadata: `PackageNotFoundError: blackout-server`. |
| PASS | `python scripts-dev/check_marker_budget.py` | `Marker budget check passed: current=96, budget=503.` |
| PASS | `rg -n "health|ready|liveness" synapse docs` | Command executes; output is broad because it matches generic words like `already`/`ready` in non-health contexts. |

Note: For health-endpoint-focused signal with less noise, use:

```bash
rg -n "(/health|health endpoint|ready endpoint|liveness)" synapse docs
```


### 1.8 Deployability unblocker rerun (2026-03-06, in-repo remediations)

| Status | Command | Result |
|---|---|---|
| PASS | `python -m synapse.app.homeserver --help` | Startup CLI now executes in source-tree mode without installed wheel metadata; it falls back to `pyproject.toml` version and skips metadata-only dependency checks. |
| PASS | `python scripts-dev/federation_client.py --help` | Script now starts without `srvlookup` installed by using optional resolver backends/fallback behavior. |

## 2) Blockers table

| Blocker | Severity | Owner | Next action date |
|---|---|---|---|
| PostgreSQL backup tooling (`pg_basebackup`, `pg_verifybackup`, `pg_controldata`) unavailable in current container, blocking runtime backup/restore drill execution. | High | Database Reliability Lead | 2026-03-11 |
| No deployed homeserver instance/config in this environment for end-to-end auth/room API smoke tests. | High | SRE Lead | 2026-03-11 |
| Runtime regression invocation in this container still does not resolve `blackout_runtime` under `pytest` collection defaults; use module-path invocation or install editable package before running that subset. | Medium | Core Server Maintainers | 2026-03-12 |

## 3) Recommendation

**Recommendation: NOT DEPLOYABLE from this environment alone.**

Rationale:
- Build/runtime toolchain binaries are present, and static runtime guardrails pass.
- Core deployment validation steps (startup, API smoke, federation smoke, backup/restore runtime execution) are blocked by environment/dependency gaps in this container.
- Deployment decision should be re-evaluated after executing the non-runnable command set in staging/production-like infrastructure with required dependencies installed.
