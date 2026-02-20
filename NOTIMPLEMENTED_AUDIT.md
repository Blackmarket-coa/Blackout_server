# NotImplementedError audit (`synapse/`)

This audit classifies each `raise NotImplementedError()` site as:
- **A**: valid abstract/interface/cache-sentinel site.
- **B**: concrete runtime gap.

## Disposition by file

| File | Classification | Disposition |
|---|---|---|
| `synapse/federation/send_queue.py` | **B** (runtime path) | Fixed: `FederationRemoteSendQueue.notify_new_events` is now a safe no-op with debug logging (event PDUs flow over events stream). |
| `synapse/federation/sender/__init__.py` | **B** (runtime path) | Fixed: `FederationSender.federation_ack` is now a safe no-op with debug logging to avoid raw `NotImplementedError` on replication paths. |
| `synapse/storage/util/id_generators.py` | **A** | `AbstractStreamIdGenerator` abstract interface methods. |
| `synapse/storage/databases/main/presence.py` | **A** | Cache descriptor sentinel for `cachedList`; explicit placeholder comment retained/clarified. |
| `synapse/storage/databases/main/end_to_end_keys.py` | **A** | Cache descriptor sentinel for bulk cross-signing key fetch; placeholder comment clarified. |
| `synapse/storage/databases/main/pusher.py` | **A** | Cache descriptor sentinel for bulk pusher lookup; placeholder comment clarified. |
| `synapse/storage/databases/main/keys.py` | **A** | Cache descriptor sentinels for bulk server-key lookups; placeholder comments clarified. |
| `synapse/storage/databases/main/signatures.py` | **A** | Cache descriptor sentinel for bulk reference-hash lookups. |
| `synapse/storage/databases/main/room.py` | **A** | Abstract background-update hook (`set_room_is_public`) on worker store split. |
| `synapse/events/__init__.py` | **A** | `EventBase.event_id` abstract property contract, implemented by concrete event types. |
| `synapse/http/server.py` | **A** | `_AsyncResource` abstract response hooks. |
| `synapse/http/connectproxyclient.py` | **A** | `ProxyCredentials` abstract interface. |
| `synapse/handlers/admin.py` | **A** | `ExfiltrationWriter` abstract writer interface methods. |
| `synapse/handlers/ui_auth/checkers.py` | **A** | `UserInteractiveAuthChecker` abstract auth-checker interface methods. |
| `synapse/handlers/oidc.py` | **A** | `OidcMappingProvider` abstract mapping provider contract methods. |
| `synapse/handlers/sso.py` | **A** | `SsoIdentityProvider` abstract redirect contract. |
| `synapse/handlers/room_member.py` | **A** | Abstract room-member federation hooks. |
| `synapse/api/auth/base.py` | **A** | Base auth interface (`is_server_admin`) for concrete auth backends. |
| `synapse/streams/__init__.py` | **A** | `EventSource` abstract stream interface. |
| `synapse/media/_base.py` | **A** | `Responder` abstract media responder interface. |
| `synapse/push/__init__.py` | **A** | `Pusher` abstract lifecycle hooks. |
| `synapse/replication/tcp/streams/_base.py` | **A** | Base stream token hooks; intentionally abstract per inline comment. |

## Regression tests added

- `tests/federation/test_federation_sender.py::FederationSenderNotImplementedRegressionTests::test_main_process_federation_ack_is_safe_noop`
- `tests/federation/test_federation_sender.py::FederationSenderNotImplementedRegressionTests::test_remote_send_queue_notify_new_events_is_safe_noop`
