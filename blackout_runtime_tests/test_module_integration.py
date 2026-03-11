from __future__ import annotations

import asyncio
import io

import pytest

from synapse.api.errors import SynapseError

from blackout_runtime.module import (
    BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE,
    BlackoutPresenceResource,
    BlackoutRuntimeModule,
)
from blackout_runtime.server_semantics import (
    BLACKOUT_CHANNEL_TYPE_EVENT,
    GOVERNANCE_PROPOSAL_EVENT,
    BlackoutPresenceService,
)


class _DummyUser:
    def __init__(self, user_id: str):
        self._user_id = user_id

    def to_string(self) -> str:
        return self._user_id


class _DummyRequester:
    def __init__(self, user_id: str):
        self.user = _DummyUser(user_id)


class _DummyEvent:
    def __init__(self, event_type: str, content: dict):
        self.type = event_type
        self.content = content


class _DummyStateEvent:
    def __init__(self, content: dict):
        self.content = content


class _DummyRequest:
    def __init__(self, body: bytes = b""):
        self.content = io.BytesIO(body)


class _FakeAccountDataManager:
    def __init__(self):
        self._store: dict[tuple[str, str], dict] = {}

    async def get_global(self, user_id: str, data_type: str):
        return self._store.get((user_id, data_type))

    async def put_global(self, user_id: str, data_type: str, new_data: dict):
        self._store[(user_id, data_type)] = dict(new_data)


class _FakeModuleApi:
    def __init__(self):
        self.callbacks = {}
        self.resources = {}
        self.account_data_manager = _FakeAccountDataManager()
        self._requester = _DummyRequester("@alice:test")

    def register_third_party_rules_callbacks(self, **kwargs):
        self.callbacks.update(kwargs)

    def register_web_resource(self, path, resource):
        self.resources[path] = resource

    async def get_user_by_req(self, request):
        del request
        return self._requester


def test_module_registers_callbacks_and_presence_resource() -> None:
    api = _FakeModuleApi()
    BlackoutRuntimeModule({}, api)

    assert "on_create_room" in api.callbacks
    assert "check_event_allowed" in api.callbacks
    assert "/_synapse/client/blackout/presence" in api.resources


def test_on_create_room_callback_applies_template_state() -> None:
    api = _FakeModuleApi()
    module = BlackoutRuntimeModule({}, api)

    config = {"creation_content": {"m.blackout.channel.type": "governance"}}
    asyncio.run(module.on_create_room(api._requester, config, False))

    initial_state = config["initial_state"]
    by_type = {entry["type"]: entry["content"] for entry in initial_state}
    assert by_type["m.room.join_rules"]["join_rule"] == "invite"
    assert by_type["m.room.power_levels"]["state_default"] == 100
    assert by_type[BLACKOUT_CHANNEL_TYPE_EVENT]["channel_type"] == "governance"


def test_on_create_room_invalid_channel_raises_synapse_403() -> None:
    api = _FakeModuleApi()
    module = BlackoutRuntimeModule({}, api)

    with pytest.raises(SynapseError, match="Unsupported blackout channel type") as exc:
        asyncio.run(module.on_create_room(
            api._requester,
            {"creation_content": {"m.blackout.channel.type": "invalid"}},
            False,
        ))

    assert exc.value.code == 403


def test_check_event_allowed_rejects_bad_governance_payload() -> None:
    api = _FakeModuleApi()
    module = BlackoutRuntimeModule({}, api)

    with pytest.raises(SynapseError, match="missing required fields") as exc:
        asyncio.run(module.check_event_allowed(
            _DummyEvent(GOVERNANCE_PROPOSAL_EVENT, {"proposal_id": "p1"}),
            {(BLACKOUT_CHANNEL_TYPE_EVENT, ""): _DummyStateEvent({"channel_type": "governance"})},
        ))

    assert exc.value.code == 403


def test_presence_resource_auth_allowed_states_and_persistence() -> None:
    api = _FakeModuleApi()
    resource = BlackoutPresenceResource(api, BlackoutPresenceService())

    code, body = asyncio.run(
        resource._async_render_PUT(_DummyRequest(b'{"state": "delivering"}'))
    )
    assert code == 200
    assert body["state"] == "delivering"

    stored = asyncio.run(api.account_data_manager.get_global(
        "@alice:test", BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE
    ))
    assert stored == {"state": "delivering"}

    # New resource instance should reload from account data (persistence semantics).
    restored_resource = BlackoutPresenceResource(api, BlackoutPresenceService())
    code, body = asyncio.run(restored_resource._async_render_GET(_DummyRequest()))
    assert code == 200
    assert body == {"user_id": "@alice:test", "state": "delivering"}

    with pytest.raises(SynapseError, match="Unsupported blackout presence state") as exc:
        asyncio.run(resource._async_render_PUT(_DummyRequest(b'{"state": "online"}')))

    assert exc.value.code == 400
