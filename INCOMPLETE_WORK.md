# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers (excluding this inventory file): **507**
- Top directories by marker count:
  - `synapse/`: **428**
  - `tests/`: **40**
  - `docs/`: **15**
  - `contrib/`: **12**
  - `scripts-dev/`: **8**

## Representative examples to prioritize

### Disabled or unfinished tests

- `tests/federation/test_federation_sender.py:488` (known stream-ID discontinuity in sender test setup)
- `tests/handlers/test_room_member.py:454` (missing cache invalidation coverage when joining after forget)
- `tests/rest/client/test_profile.py:172` (FIXME around profile display name behavior)

### NotImplemented placeholders in production code paths

- `synapse/storage/databases/main/relations.py:469` (`raise NotImplementedError()`)
- `synapse/storage/databases/main/relations.py:523` (`raise NotImplementedError()`)
- `synapse/storage/databases/main/relations.py:610` (`raise NotImplementedError()`)

### Known tech debt called out with FIXMEs

- `synapse/handlers/deactivate_account.py:91` (race condition note)
- `synapse/federation/federation_client.py:1277` (signature failure handling)
- `synapse/media/url_previewer.py:481` (error passthrough behavior)

## Command used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```
