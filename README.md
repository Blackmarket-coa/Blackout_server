# Blackout Server

Blackout Server is a Matrix homeserver distribution built on Synapse and tailored for Blackout's signaling-first architecture. It keeps Synapse compatibility while adding Blackout-specific runtime controls, reliability tracking artifacts, and operator playbooks for constrained deployments (including phone-hosted and low-resource nodes).

For the long-form RST overview, see [`README.rst`](README.rst).

## What this project is for

Blackout Server is designed for teams that need Matrix interoperability **and** tighter control over signaling behavior, resource usage, and operational reliability.

Typical goals:

- Run a Matrix-compatible server with Blackout-specific signaling controls.
- Enforce safety constraints in blackout mode (validation, event gating, key-revocation checks).
- Operate reliably on constrained infrastructure via documented runbooks and deployment profiles.
- Track implementation scope and completion status through maintained planning/reporting docs.

## Core features

### 1. Signaling-first blackout mode

When enabled (`blackout.enabled: true`), the server can enforce a signaling-only operating profile, including acceptance of `m.blackout.signal` events and rejection of unsupported timeline traffic for blackout mode.

- Feature overview: [`README.rst`](README.rst)
- Signaling persistence policy: [`docs/signaling_only_persistence_policy.md`](docs/signaling_only_persistence_policy.md)

### 2. Strict signaling payload validation

Blackout signal payloads are validated against expected schema shape (e.g., ICE/SDP and related metadata fields) to reduce malformed signaling traffic entering rooms.

- Runtime envelope/validation primitives: [`blackout_runtime/envelope.py`](blackout_runtime/envelope.py)
- Runtime tests: [`blackout_runtime_tests/test_envelope.py`](blackout_runtime_tests/test_envelope.py)

### 3. Signal event expiry controls

The Blackout model includes signal event TTL controls (`blackout.signal_event_ttl`) to keep transient signaling data from accumulating indefinitely.

- Configuration/behavior description: [`README.rst`](README.rst)
- Message retention guidance: [`docs/message_retention_policies.md`](docs/message_retention_policies.md)

### 4. Compromised-device protection posture

Blackout controls include sender/device trust protections, including revocation-aware handling for signaling ingress.

- Operational and reliability documentation: [`docs/blackout-ops-runbook.md`](docs/blackout-ops-runbook.md)
- Incident/process maturity context: [`docs/incident_response_maturity.md`](docs/incident_response_maturity.md)

### 5. Low-resource operational profile

Blackout mode is documented with low-resource defaults and operating recommendations for constrained environments.

- TURN/STUN and constrained networking guidance: [`docs/turn-howto.md`](docs/turn-howto.md)
- Docker deployment references: [`docker/README.md`](docker/README.md), [`contrib/docker/README.md`](contrib/docker/README.md)

### 6. Reliability, scope, and completion tracking

This repository includes explicit artifacts for feature parity planning, backend plan tracking, weekly reporting, and completion gates.

- Upstream feature parity matrix: [`docs/development/blackout_upstream_feature_matrix.md`](docs/development/blackout_upstream_feature_matrix.md)
- Backend tracker: [`docs/development/blackout_backend_plan_tracker.md`](docs/development/blackout_backend_plan_tracker.md)
- Completion tracker: [`docs/project_completion_tracker.md`](docs/project_completion_tracker.md)
- Weekly reports: [`docs/reports/`](docs/reports/)

## How it works (high level)

Blackout Server follows Synapse architecture and extends behavior through configuration, runtime validation utilities, and operations standards.

1. **Synapse-compatible base runtime**
   - The project packages Synapse server applications (`synapse_homeserver`, workers, and admin scripts) and retains standard Matrix homeserver behavior where not explicitly constrained.

2. **Blackout runtime controls**
   - Blackout-specific runtime modules provide envelope handling, readiness helpers, and CRDT/runtime helpers used by the Blackout workstream.

3. **Config-driven mode switching**
   - Blackout behavior is feature-flag/config driven (e.g., `blackout.enabled`, signal TTL), allowing rollout and rollback through configuration changes.

4. **Ops-first governance model**
   - Documentation includes runbooks, drills, maturity reports, and scoped completion artifacts so deployment readiness can be measured and audited.

Useful technical entry points:

- Runtime package: [`blackout_runtime/`](blackout_runtime/)
- Runtime tests: [`blackout_runtime_tests/`](blackout_runtime_tests/)
- Synapse config modules: [`synapse/config/`](synapse/config/)

## Example use cases

- **Secure signaling backbone for constrained clients**  
  Deploy Blackout Server as a Matrix-compatible signaling layer with stricter event controls and reduced resource footprint.

- **Phone-hosted or edge-hosted federated nodes**  
  Use low-resource recommendations and TURN guidance for unstable networks, intermittent power, or limited memory.

- **Staged modernization with measurable gates**  
  Use parity matrix + completion tracker + weekly reports to manage phased implementation with explicit owner/due/evidence metadata.

- **Operations-heavy environments**  
  Apply runbooks, drills, and reliability reports to formalize incident response and deployment confidence checks.

## Installation and setup

- Synapse installation guide (project docs): [`docs/setup/installation.md`](docs/setup/installation.md)
- Upgrade guidance: [`docs/upgrade.md`](docs/upgrade.md)
- Sample config: [`docs/sample_config.yaml`](docs/sample_config.yaml)
- Docker: [`docker/README.md`](docker/README.md)

## Development and testing

- Contributing guide: [`docs/development/contributing_guide.md`](docs/development/contributing_guide.md)
- Top-level contributing pointer: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Changelog: [`CHANGES.md`](CHANGES.md)
- Developer docs root: [`docs/development/`](docs/development/)

## GitHub information

- **Repository:** <https://github.com/Blackmarket-coa/Blackout_server>
- **Upstream base project:** <https://github.com/element-hq/synapse>
- **Issues:** <https://github.com/Blackmarket-coa/Blackout_server/issues>
- **Pull Requests:** <https://github.com/Blackmarket-coa/Blackout_server/pulls>
- **License:** Apache-2.0 ([`LICENSE`](LICENSE))

### Suggested GitHub workflow

1. Create a feature branch from your default branch.
2. Make focused commits with clear scope.
3. Update docs/tests with code changes.
4. Open a PR with:
   - summary of behavior changes,
   - rollout/rollback notes,
   - validation evidence (tests/commands/log snippets),
   - links to impacted docs.

## Quick checks

```bash
python scripts-dev/check_marker_budget.py
rg -n "^- \[ \] \[required-now\]" docs/project_completion_tracker.md
rg -n "raise [N]otImplementedError\(" synapse
rg -n "U1|U12|unsupported|partial|complete" docs/development/blackout_upstream_feature_matrix.md
```
