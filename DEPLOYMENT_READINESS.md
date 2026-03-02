# Deployment Readiness Report

Date: 2026-03-02

## Scope
This report reflects a local validation pass on branch `work` focused on restoring build/tooling health and exercising the CI test matrix entrypoint.

## Tooling Remediation Performed

1. Repaired Poetry runtime dependency mismatch in the environment (`packaging`, `keyring`, `pkginfo`, `urllib3`) so Poetry commands run again.
2. Updated project dependency constraints to avoid known runtime breakages in this environment:
   - `pyOpenSSL` raised to `>=25.1.0` for compatibility with modern `cryptography` / OpenSSL bindings.
   - `prometheus-client` capped to `<0.21` to avoid MRO import failure in `synapse.metrics.InFlightGauge`.
3. Regenerated lockfile with `poetry lock`.

## Checks Run

- `poetry --version` → passed.
- `poetry check --lock` → passed (with deprecation warnings in project metadata layout).
- `tox` → started full matrix and reported missing local interpreters for `py37`, `py38`, `py39`.
- `tox -r -e py310` → executed a broad test sweep and surfaced many failing tests (both FAIL and ERROR).

## Assessment

Current status: **Not ready for deployment**.

Reasoning:

1. CI-equivalent matrix cannot be fully executed in this environment due missing Python interpreters (3.7/3.8/3.9).
2. The available `py310` run now executes, but reports numerous test failures across federation, handlers, and blackout-related suites.
3. Until those failures are triaged/fixed and the full matrix passes in CI, production deployment is high risk.

## Required Next Gates

1. Run full CI in an environment that includes all required Python versions.
2. Triage and resolve failing `py310` test suites discovered by tox.
3. Re-run the full matrix until all required jobs are green.
4. Execute staging smoke tests (startup, DB/migrations, federation flows, workers) before prod cutover.
