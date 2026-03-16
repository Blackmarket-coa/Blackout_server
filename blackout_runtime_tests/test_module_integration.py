from __future__ import annotations

import asyncio
import io
import tempfile
import os

import pytest

from synapse.api.errors import SynapseError

from blackout_runtime.module import BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE, BlackoutRuntimeModule
from blackout_runtime.server_semantics import BLACKOUT_CHANNEL_TYPE_EVENT, GOVERNANCE_PROPOSAL_EVENT


class _DummyUser:
    def __init__(self, user_id: str):
        self._user_id = user_id

    def to_string(self) -> str:
        return self._user_id


class _DummyRequester:
    def __init__(self, user_id: str):
        self.user = _DummyUser(user_id)


class _DummyEvent:
    def __init__(
        self,
        event_type: str,
        content: dict,
        room_id: str = "!r:test",
        sender: str = "@alice:test",
        event_id: str = "$event",
    ):
        self.type = event_type
        self.content = content
        self.room_id = room_id
        self.sender = sender
        self.event_id = event_id
        self.origin_server_ts = 1


class _DummyStateEvent:
    def __init__(self, content: dict):
        self.content = content


class _DummyRequest:
    def __init__(self, body: bytes = b"", args: dict[bytes, list[bytes]] | None = None):
        self.content = io.BytesIO(body)
        self.args = args or {}


class _FakeAccountDataManager:
    def __init__(self):
        self._store: dict[tuple[str, str], dict] = {}

    async def get_global(self, user_id: str, data_type: str):
        return self._store.get((user_id, data_type))

    async def put_global(self, user_id: str, data_type: str, new_data: dict):
        self._store[(user_id, data_type)] = dict(new_data)


class _FakeDbPool:
    async def runInteraction(self, desc, func):
        del desc
        class T:
            def execute(self, sql, args):
                self.rows = []
            def __iter__(self):
                return iter([])
        return func(T())


class _FakeStore:
    db_pool = _FakeDbPool()

    def get_room_max_token(self):
        return "unused"

    async def get_recent_events_for_room(self, room_id, limit, end_token):
        del room_id, limit, end_token
        return [], None

    async def get_events_as_list(self, event_ids):
        del event_ids
        return []


class _FakeModuleApi:
    def __init__(self):
        self.callbacks = {}
        self.resources = {}
        self.account_data_manager = _FakeAccountDataManager()
        self._requester = _DummyRequester("@alice:test")
        self._store = _FakeStore()

    def register_third_party_rules_callbacks(self, **kwargs):
        self.callbacks.update(kwargs)

    def register_web_resource(self, path, resource):
        self.resources[path] = resource

    async def get_user_by_req(self, request):
        del request
        return self._requester


def _build_module(api: _FakeModuleApi) -> BlackoutRuntimeModule:
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    return BlackoutRuntimeModule({"persistence_path": path}, api)


def test_module_registers_callbacks_and_blackout_resource_tree() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    assert "on_create_room" in api.callbacks
    assert "check_event_allowed" in api.callbacks
    assert "on_new_event" in api.callbacks
    assert "/_synapse/client/blackout" in api.resources
    assert module is not None


def test_on_create_room_callback_applies_template_state() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    config = {"creation_content": {"m.blackout.channel.type": "governance"}}
    asyncio.run(module.on_create_room(api._requester, config, False))

    initial_state = config["initial_state"]
    by_type = {entry["type"]: entry["content"] for entry in initial_state}
    assert by_type["m.room.join_rules"]["join_rule"] == "invite"
    assert by_type["m.room.power_levels"]["state_default"] == 100
    assert by_type[BLACKOUT_CHANNEL_TYPE_EVENT]["channel_type"] == "governance"


def test_on_create_room_callback_wires_dead_drop_preset() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    config = {"preset": "blackout_dead_drop_room"}
    asyncio.run(module.on_create_room(api._requester, config, False))

    assert config["creation_content"]["m.blackout.channel.type"] == "blackout_dead_drop_room"
    initial_state = {entry["type"]: entry["content"] for entry in config["initial_state"]}
    assert initial_state["m.room.join_rules"]["join_rule"] == "invite"
    assert initial_state["m.room.history_visibility"]["history_visibility"] == "joined"

def test_check_event_allowed_rejects_bad_governance_payload_and_duplicate_vote() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    with pytest.raises(SynapseError, match="missing required fields"):
        asyncio.run(
            module.check_event_allowed(
                _DummyEvent(GOVERNANCE_PROPOSAL_EVENT, {"proposal_id": "p1"}),
                {(BLACKOUT_CHANNEL_TYPE_EVENT, ""): _DummyStateEvent({"channel_type": "governance"})},
            )
        )

    asyncio.run(
        module.on_new_event(
            _DummyEvent(
                "m.blackout.governance.vote",
                {"proposal_id": "p1", "vote": "yes", "decision": "accepted"},
                room_id="!gov:test",
                sender="@alice:test",
                event_id="$vote1",
            ),
            {},
        )
    )

    with pytest.raises(SynapseError, match="Only one vote"):
        asyncio.run(
            module.check_event_allowed(
                _DummyEvent(
                    "m.blackout.governance.vote",
                    {"proposal_id": "p1", "vote": "no"},
                    room_id="!gov:test",
                    sender="@alice:test",
                    event_id="$vote2",
                ),
                {(BLACKOUT_CHANNEL_TYPE_EVENT, ""): _DummyStateEvent({"channel_type": "governance"})},
            )
        )


def test_presence_and_blackout_synapse_api_resources() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)
    root = api.resources["/_synapse/client/blackout"]

    presence = root.children[b"presence"]
    code, body = asyncio.run(presence._async_render_PUT(_DummyRequest(b'{"state":"delivering"}')))
    assert code == 200
    assert body["state"] == "delivering"

    stored = asyncio.run(api.account_data_manager.get_global("@alice:test", BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE))
    assert stored == {"state": "delivering"}

    asyncio.run(
        module.on_new_event(
            _DummyEvent(
                "m.blackout.governance.vote",
                {"proposal_id": "p1", "vote": "yes", "decision": "accepted"},
                room_id="!gov:test",
                sender="@alice:test",
                event_id="$v1",
            ),
            {},
        )
    )

    decisions_resource = root.children[b"governance"].children[b"decisions"]
    code, body = asyncio.run(decisions_resource._async_render_GET(_DummyRequest(args={b"room_id": [b"!gov:test"], b"since": [b"0"]})))
    assert code == 200
    assert body["decisions"][0]["decision"] == "accepted"

    reputation_root = root.children[b"reputation"]
    node_resource = reputation_root.getChild(b"node-1", _DummyRequest())
    code, body = asyncio.run(node_resource._async_render_GET(_DummyRequest()))
    assert code == 200
    assert body["node_id"] == "node-1"


def test_dead_drop_retention_purge_schedules_and_purges_by_ttl() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    state_events = {(BLACKOUT_CHANNEL_TYPE_EVENT, ""): _DummyStateEvent({"channel_type": "blackout_dead_drop_room"})}

    asyncio.run(
        module.on_new_event(
            _DummyEvent(
                "m.room.message",
                {"body": "expired"},
                room_id="!dd:test",
                sender="@alice:test",
                event_id="$dd1",
            ),
            state_events,
        )
    )
    asyncio.run(
        module.on_new_event(
            _DummyEvent(
                "m.room.message",
                {"body": "fresh"},
                room_id="!dd:test",
                sender="@alice:test",
                event_id="$dd2",
            ),
            state_events,
        )
    )

    module._conn.execute(
        "UPDATE blackout_dead_drop_retention SET expires_at_ms = ? WHERE event_id = ?",
        (1_000, "$dd1"),
    )
    module._conn.execute(
        "UPDATE blackout_dead_drop_retention SET expires_at_ms = ? WHERE event_id = ?",
        (9_999_999, "$dd2"),
    )
    module._conn.commit()

    purged = module.run_dead_drop_purge(now_ms=2_000)
    assert [item["event_id"] for item in purged] == ["$dd1"]
    assert purged[0]["tombstone_event_type"] == "m.room.tombstone"

    dd1 = module.get_dead_drop_retention_record("$dd1")
    dd2 = module.get_dead_drop_retention_record("$dd2")
    assert dd1 is not None and dd1["purged_at_ms"] == 2_000
    assert dd2 is not None and dd2["purged_at_ms"] is None


def test_announcement_room_sender_restrictions_enforced() -> None:
    api = _FakeModuleApi()
    module = _build_module(api)

    restricted_state = {
        (BLACKOUT_CHANNEL_TYPE_EVENT, ""): _DummyStateEvent({"channel_type": "blackout_announcement_room"}),
        ("m.room.power_levels", ""): _DummyStateEvent(
            {
                "events": {"m.room.message": 50},
                "users": {"@announcer:test": 100, "@member:test": 0},
            }
        ),
    }

    with pytest.raises(SynapseError, match="not permitted"):
        asyncio.run(
            module.check_event_allowed(
                _DummyEvent(
                    "m.room.message",
                    {"body": "unauthorized"},
                    room_id="!announce:test",
                    sender="@member:test",
                    event_id="$msg1",
                ),
                restricted_state,
            )
        )

    allowed, replacement_dict = asyncio.run(
        module.check_event_allowed(
            _DummyEvent(
                "m.room.message",
                {"body": "authorized"},
                room_id="!announce:test",
                sender="@announcer:test",
                event_id="$msg2",
            ),
            restricted_state,
        )
    )
    assert allowed is True
    assert replacement_dict is None
