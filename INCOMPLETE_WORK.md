# Incomplete work inventory

This file was generated from a quick source scan for common incomplete-work markers
(`TODO`, `FIXME`, `TBD`, `XXX`, `HACK`, `NotImplementedError`, and `TODO_test_*`).

## High-level totals

- Total potential incomplete-work markers: **510**
- Top directories by marker count:
  - `synapse/`: **428**
  - `tests/`: **43**
  - `docs/`: **15**
  - `contrib/`: **12**
  - `scripts-dev/`: **8**

## Representative examples to prioritize

### Disabled or unfinished tests

- `tests/rest/client/test_events.py:117` (`def TODO_test_stream_items`) 
- `tests/federation/test_federation_sender.py:306` (test comment indicates expected failure path not yet enforced)
- `tests/handlers/test_room_member.py:211` (missing rate-limit test for remote joins)

### NotImplemented placeholders in production code paths

- `synapse/federation/federation_server.py:579` (`raise NotImplementedError("Specify an event")`)
- `synapse/storage/databases/main/room.py:1937` (`raise NotImplementedError()`)
- `synapse/storage/databases/main/relations.py:469` (`raise NotImplementedError()`)

### Known tech debt called out with FIXMEs

- `synapse/handlers/deactivate_account.py:91` (race condition note)
- `synapse/federation/federation_client.py:1277` (signature failure handling)
- `synapse/media/url_previewer.py:481` (error passthrough behavior)

## Command used

```bash
rg -n "TODO|FIXME|TBD|XXX|HACK|NotImplementedError|TODO_test_stream_items" .
```
