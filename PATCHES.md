# Local Synapse Fork Patches

This repository tracks upstream Synapse while carrying Blackout-specific extensions.

## Upstream sync discipline

1. Configure the canonical upstream remote:
   ```bash
   git remote add upstream https://github.com/element-hq/synapse.git
   ```
2. Merge upstream `develop` monthly, and immediately for security advisories.
3. Keep Blackout features isolated to `blackout_runtime/` and `blackout_runtime_tests/` wherever possible.
4. Document any unavoidable edits outside those directories in this file before merge/rebase.

## Current non-upstreamed patch surface

- `blackout_runtime/`: Blackout module semantics and APIs.
- `blackout_runtime_tests/`: Blackout runtime + integration tests.
- Project docs (`DEPLOYMENT_READINESS.md`, `docs/bmc_server_execution_plan.md`): rollout tracking and implementation planning.

No direct core Synapse source modifications are currently required for the Blackout module callback wiring in this phase.
