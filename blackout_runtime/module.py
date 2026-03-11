from __future__ import annotations

import json
from typing import Any, Mapping, MutableMapping, Optional

from synapse.api.errors import SynapseError
from synapse.http.server import DirectServeJsonResource
from synapse.http.site import SynapseRequest
from synapse.types import JsonDict, StateMap

from .server_semantics import (
    BLACKOUT_CHANNEL_TYPE_EVENT,
    BLACKOUT_PRESENCE_ROUTE,
    BlackoutPresenceService,
    BlackoutServerSemantics,
)

BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE = "m.blackout.presence"


class BlackoutPresenceResource(DirectServeJsonResource):
    def __init__(self, module_api: Any, presence: BlackoutPresenceService):
        super().__init__()
        self._module_api = module_api
        self._presence = presence

    async def _async_render_GET(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        requester = await self._module_api.get_user_by_req(request)
        user_id = requester.user.to_string()

        state = self._presence.get_presence(user_id)
        if state is None:
            stored = await self._module_api.account_data_manager.get_global(
                user_id, BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE
            )
            if isinstance(stored, Mapping):
                stored_state = stored.get("state")
                if isinstance(stored_state, str):
                    self._presence.set_presence(user_id, stored_state)
                    state = stored_state

        return 200, {"user_id": user_id, "state": state}

    async def _async_render_PUT(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        requester = await self._module_api.get_user_by_req(request)
        user_id = requester.user.to_string()

        try:
            body = self._parse_json_body(request)
        except ValueError as exc:
            raise SynapseError(400, str(exc))

        state = body.get("state")
        if not isinstance(state, str):
            raise SynapseError(400, "Request body must include string field 'state'")

        try:
            self._presence.set_presence(user_id, state)
        except ValueError as exc:
            raise SynapseError(400, str(exc))

        await self._module_api.account_data_manager.put_global(
            user_id,
            BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE,
            {"state": state},
        )

        return 200, {"user_id": user_id, "state": state}

    @staticmethod
    def _parse_json_body(request: SynapseRequest) -> JsonDict:
        raw = request.content.read()
        if not raw:
            raise ValueError("Request body must be JSON")

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Malformed JSON in request body") from exc

        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object")

        return body


class BlackoutRuntimeModule:
    """Synapse module integration for blackout runtime semantics."""

    def __init__(self, config: JsonDict, module_api: Any):
        self._config = config
        self._module_api = module_api
        self._semantics = BlackoutServerSemantics()
        self._presence = BlackoutPresenceService()

        self._module_api.register_third_party_rules_callbacks(
            on_create_room=self.on_create_room,
            check_event_allowed=self.check_event_allowed,
        )
        self._module_api.register_web_resource(
            BLACKOUT_PRESENCE_ROUTE,
            BlackoutPresenceResource(self._module_api, self._presence),
        )

    async def on_create_room(
        self,
        requester: Any,
        config: MutableMapping[str, object],
        is_requester_admin: bool,
    ) -> None:
        del requester, is_requester_admin
        try:
            self._semantics.on_create_room(config)
        except ValueError as exc:
            raise SynapseError(403, str(exc))

    async def check_event_allowed(
        self,
        event: Any,
        state_events: StateMap[Any],
    ) -> tuple[bool, Optional[dict]]:
        channel_type = self._extract_channel_type(state_events)

        try:
            self._semantics.check_event_allowed(
                event.type,
                event.content,
                channel_type=channel_type,
            )
        except ValueError as exc:
            raise SynapseError(403, str(exc))

        return True, None

    @staticmethod
    def _extract_channel_type(state_events: StateMap[Any]) -> str | None:
        event = state_events.get((BLACKOUT_CHANNEL_TYPE_EVENT, ""))
        if event is None:
            return None

        content = getattr(event, "content", None)
        if not isinstance(content, Mapping):
            return None

        channel_type = content.get("channel_type")
        return channel_type if isinstance(channel_type, str) else None
