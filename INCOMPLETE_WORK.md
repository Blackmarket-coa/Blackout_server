# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers (excluding this inventory file): **496**
- Top directories by marker count:
  - `synapse/`: **420**
  - `tests/`: **37**
  - `docs/`: **15**
  - `contrib/`: **12**
  - `scripts-dev/`: **8**

## Representative examples to prioritize

### Disabled or unfinished tests

- `tests/rest/client/test_profile.py:172` (FIXME around profile display name behavior)
- `tests/rest/client/test_profile.py:182` (FIXME around profile avatar URL behavior)
- `tests/federation/test_federation_server.py:262` (TODO to improve auth-chain test coverage)

### NotImplemented placeholders (primarily abstract/interface stubs)

- `synapse/storage/databases/main/room.py:1937` (`raise NotImplementedError()` abstract store method)
- `synapse/storage/util/id_generators.py:116` (`raise NotImplementedError()` abstract stream ID interface)
- `synapse/handlers/sso.py:130` (`raise NotImplementedError()` abstract IdP redirect handler)

### Known tech debt called out with FIXMEs

- `synapse/handlers/deactivate_account.py:91` (race condition note)
- `synapse/federation/federation_client.py:1277` (signature failure handling)
- `synapse/media/url_previewer.py:481` (error passthrough behavior)

## Command used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_" .
```
