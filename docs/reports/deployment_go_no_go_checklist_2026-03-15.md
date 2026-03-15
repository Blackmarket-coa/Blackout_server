# Deployment go/no-go checklist (strict pass)

- Date: `2026-03-15`
- Evaluator: `Codex deployment audit`
- Branch: `work`

## Verdict

**Go/No-Go recommendation: NO-GO**.

Reason: core runtime boot and schema update checks succeed, but targeted smoke tests include reproducible failures, Poetry health remains broken in this environment, and program-level release backlog/open blockers remain high.

## Checklist results

| Gate | Command / evidence | Result | Notes |
|---|---|---|---|
| Runtime boot (single-node) | `python -m synapse.app.homeserver --generate-config ...` then run and probe `/_matrix/client/versions` on localhost | ✅ Pass | Server generated config, started, and served versions API. |
| DB schema update (dry-run equivalent) | `python -m synapse._scripts.update_synapse_database --database-config <generated homeserver.yaml>` (run twice) | ✅ Pass | First run initializes/updates schema; second run confirms idempotent "schema now up to date" behavior. |
| Smoke test: homeserver startup test | `python -m pytest -q tests/app/test_homeserver_start.py` | ✅ Pass | 1 passed. |
| Smoke test: OpenID listener test slice | `python -m pytest -q tests/app/test_openid_listener.py` | ❌ Fail | 4 failures in `FederationReaderOpenIDListenerTests` with `UpgradeDatabaseException` (uninitialised DB on worker). |
| Tooling gate: Poetry health | `poetry --version` and `poetry check --lock` | ❌ Fail | Environment reports `No module named 'packaging.licenses'`. |
| Delivery readiness backlog gate | `docs/reports/weekly_completion_report_2026-03-21.md` + tracker count script | ❌ Fail | `Required-now` open items: 61; multiple active blockers and most BLK-101..120 items are not complete. |

## Minimal canary criteria and assessment

Canary criteria used for this strict pass:

1. **Boot/health criterion**: fresh config instance must start and answer `/versions` within 60s.
2. **Schema criterion**: DB update command must complete successfully and be idempotent on immediate re-run.
3. **Targeted smoke criterion**: startup test and OpenID listener suite both green.
4. **Tooling criterion**: lockfile validity checkable via Poetry.
5. **Program criterion**: no critical release blockers and required-now backlog below emergency threshold.

Assessment:

- Criteria 1 and 2: **met**.
- Criteria 3, 4, and 5: **not met**.

## Deployment risk score

Scale: `0` = minimal risk, `100` = extreme release risk.

- Runtime boot health: `10/100` risk contribution (low; passed).
- DB migration behavior: `10/100` risk contribution (low; passed).
- Smoke tests (targeted app slice): `25/100` risk contribution (high; failures present).
- Tooling/packaging health: `20/100` risk contribution (high; Poetry broken).
- Program delivery readiness (open required-now and blockers): `20/100` risk contribution (high).

**Overall deployment risk score: `85/100` (high risk, no-go).**

## Recommended next actions before re-evaluation

1. Repair Poetry runtime environment so lockfile and dependency validation gates run consistently.
2. Triage and fix `tests/app/test_openid_listener.py` failures (`UpgradeDatabaseException` path for worker startup).
3. Re-run strict checklist with full CI matrix (including missing interpreter lanes) and attach green evidence.
4. Burn down `required-now` execution backlog and explicitly close listed blockers in weekly report/tracker.
