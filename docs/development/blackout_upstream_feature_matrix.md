# Blackout upstream feature support matrix (server)

_Date: 2026-03-02_

This matrix tracks current `Blackout_server` support for upstream Blackout features (`U1`-`U12`) defined in `docs/upstream_blackout_feature_build_plan.md`.

Support status legend:
- `unsupported`: no shipped server implementation path for the upstream feature family.
- `partial`: some artifacts/controls exist, but end-to-end feature support is not complete.
- `complete`: feature family has end-to-end implementation and validation evidence.

| ID | Feature family | Scope class | Support status | Owner | Due | Measurable exit criteria | Evidence path |
|---|---|---|---|---|---|---|---|
| U1 | Steganography core pipeline | required-now | complete | Protocol Engineer | 2026-03-29 | `m.blackout.signal` stego metadata envelope is validated and policy-gated with pass/fail coverage. | `docs/policy_schemas/blackout_signal_stego.schema.json`; `synapse/util/blackout.py`; `tests/blackout_runtime/test_module_e2e.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U2 | Stego entitlements | required-now | complete | Security Engineer | 2026-03-29 | Sender-level stego entitlements are enforced before accepting stego-enabled signaling payloads. | `blackout_runtime/module.py`; `tests/blackout_runtime/test_module_e2e.py`; `blackout_runtime_tests/test_module_integration.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U3 | Paid rooms / boosts integration | required-later | partial | Product Integrations Lead | 2026-04-30 | Paid-room/boost flags are represented in server state, config-gated, and validated with abuse controls plus integration tests. | `docs/upstream_blackout_feature_build_plan.md`; `docs/development/wave2_u3_u7_u9_kickoff_plan.md`; implementation + tests (to be added) |
| U4 | Ephemeral stego policies | required-now | complete | Data Lifecycle Engineer | 2026-03-31 | Stego TTL scheduling + bounded purge flow is implemented and validated with retention tests. | `blackout_runtime/module.py`; `blackout_runtime_tests/test_module_integration.py`; `tests/blackout_runtime/test_module_e2e.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U5 | Stego plugin surface | required-later | unsupported | Extension Platform Lead | 2026-05-15 | Plugin metadata contract + signature verification policy are documented and conformance tested. | `docs/upstream_blackout_feature_build_plan.md`; contract + tests (to be added) |
| U6 | Governance services | required-now | complete | Governance Services Lead | 2026-03-31 | Governance schema validation, proposal-window vote gating, and decision flows are test-backed. | `docs/policy_schemas/blackout_governance_attestation.schema.json`; `blackout_runtime/server_semantics.py`; `blackout_runtime/module.py`; `tests/blackout_runtime/test_module_e2e.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U7 | Deliberation + task workflows | required-later | partial | Workflow Services Lead | 2026-04-30 | Deliberation/task event state machine (proposal->vote->execution) is contract-defined with transition guards and test plan. | `docs/upstream_blackout_feature_build_plan.md`; `docs/development/wave2_u3_u7_u9_kickoff_plan.md`; workflow tests (to be added) |
| U8 | Delegation + attestations | required-now | complete | Identity/Trust Lead | 2026-03-31 | Delegation scope and attestation proof verification are enforced with reject/accept tests. | `docs/policy_schemas/blackout_delegation_grant.schema.json`; `docs/policy_schemas/blackout_attestation.schema.json`; `blackout_runtime/module.py`; `blackout_runtime_tests/test_module_integration.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U9 | Townhall/community modules | required-later | partial | Community Platform Lead | 2026-05-15 | Townhall session/agenda/summary contracts and moderated endpoint plan are defined with rollout/test gates. | `docs/upstream_blackout_feature_build_plan.md`; `docs/development/wave2_u3_u7_u9_kickoff_plan.md`; endpoint specs/tests (to be added) |
| U10 | P2P/self-healing transport hooks | required-now | complete | Federation Architecture Lead | 2026-03-31 | Peer-sync metadata and bootstrap/recovery envelope paths are implemented and validated by runtime tests. | `docs/policy_schemas/blackout_peer_sync_metadata.schema.json`; `docs/policy_schemas/blackout_bootstrap_recovery_envelope.schema.json`; `blackout_runtime/runtime.py`; `blackout_runtime_tests/test_runtime.py`; `blackout_runtime_tests/test_wave1_schema_contracts.py` |
| U11 | Ops evidence + SLO artifacts | required-now | complete | SRE Lead | 2026-03-21 | One-command evidence validation exists and is enforced in release-gate CI. | `scripts-dev/blackout/validate_tracker_evidence.sh`; `.github/workflows/release-train-gate.yml`; `docs/reliability_reports/`; `docs/drills/` |
| U12 | Module/runtime extensibility | required-later | unsupported | Runtime Extensibility Lead | 2026-05-15 | Extension contract and capability negotiation are versioned and validated via compatibility tests. | `docs/upstream_blackout_feature_build_plan.md`; extensibility contract/tests (to be added) |

## Notes

- This matrix is the canonical support-state view for U1-U12 and should be updated whenever feature status changes.
- For every `unsupported` or `partial` row, owner/due/exit/evidence fields are mandatory.
