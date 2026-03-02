# Blackout upstream feature support matrix (server)

_Date: 2026-03-02_

This matrix tracks current `Blackout_server` support for upstream Blackout features (`U1`-`U12`) defined in `docs/upstream_blackout_feature_build_plan.md`.

Support status legend:
- `unsupported`: no shipped server implementation path for the upstream feature family.
- `partial`: some artifacts/controls exist, but end-to-end feature support is not complete.
- `complete`: feature family has end-to-end implementation and validation evidence.

| ID | Feature family | Scope class | Support status | Owner | Due | Measurable exit criteria | Evidence path |
|---|---|---|---|---|---|---|---|
| U1 | Steganography core pipeline | required-now | unsupported | Protocol Engineer | 2026-03-29 | Server validates stego metadata envelope and policy hooks with pass/fail tests for accepted/rejected payload classes. | `docs/upstream_blackout_feature_build_plan.md`; validator/tests under `synapse/` + `tests/` |
| U2 | Stego entitlements | required-now | unsupported | Security Engineer | 2026-03-29 | Entitlement checks are enforced on stego-enabled event flows with stable error responses and tests. | `docs/upstream_blackout_feature_build_plan.md`; entitlement checks in `synapse/`; tests in `tests/` |
| U3 | Paid rooms / boosts integration | required-later | unsupported | Product Integrations Lead | 2026-04-30 | Paid-room/boost flags are represented in server state and guarded by policy checks behind config flags. | `docs/upstream_blackout_feature_build_plan.md`; implementation + tests (to be added) |
| U4 | Ephemeral stego policies | required-now | unsupported | Data Lifecycle Engineer | 2026-03-31 | Retention semantics for stego payload lifecycle are implemented and verified with TTL/purge tests. | `docs/development/blackout_retention_compliance_note.md`; retention tests under `tests/` |
| U5 | Stego plugin surface | required-later | unsupported | Extension Platform Lead | 2026-05-15 | Plugin metadata contract + signature verification policy are documented and conformance tested. | `docs/upstream_blackout_feature_build_plan.md`; contract + tests (to be added) |
| U6 | Governance services | required-now | unsupported | Governance Services Lead | 2026-03-31 | Governance event schemas and moderation/voting state transitions are implemented with API tests. | `docs/upstream_blackout_feature_build_plan.md`; schema + API tests (to be added) |
| U7 | Deliberation + task workflows | required-later | unsupported | Workflow Services Lead | 2026-04-30 | Deliberation/task event state machine (proposal->vote->execution) exists with transition validation tests. | `docs/upstream_blackout_feature_build_plan.md`; workflow tests (to be added) |
| U8 | Delegation + attestations | required-now | unsupported | Identity/Trust Lead | 2026-03-31 | Delegation authorization and attestation verification paths are enforced with reject/accept tests. | `docs/upstream_blackout_feature_build_plan.md`; authorization checks/tests (to be added) |
| U9 | Townhall/community modules | required-later | unsupported | Community Platform Lead | 2026-05-15 | Server primitives for townhall sessions/agendas/summaries are implemented with endpoint tests. | `docs/upstream_blackout_feature_build_plan.md`; endpoint specs/tests (to be added) |
| U10 | P2P/self-healing transport hooks | required-now | partial | Federation Architecture Lead | 2026-03-31 | Compatibility layer covers peer-sync metadata and bootstrap/recovery envelope parity with upstream expectations, validated by integration tests. | `docs/distributed_self_healing_blueprint.md`; `blackout_runtime/`; `blackout_runtime_tests/` |
| U11 | Ops evidence + SLO artifacts | required-now | partial | SRE Lead | 2026-03-21 | Upstream-style evidence validation script exists and verifies tracker-referenced reliability/drill artifacts in one command. | `docs/reliability_slo_instrumentation.md`; `docs/reliability_slo_alerting_and_paging.md`; `docs/reliability_reports/`; `docs/drills/` |
| U12 | Module/runtime extensibility | required-later | unsupported | Runtime Extensibility Lead | 2026-05-15 | Extension contract and capability negotiation are versioned and validated via compatibility tests. | `docs/upstream_blackout_feature_build_plan.md`; extensibility contract/tests (to be added) |

## Notes

- This matrix is the canonical support-state view for U1-U12 and should be updated whenever feature status changes.
- For every `unsupported` or `partial` row, owner/due/exit/evidence fields are mandatory.
