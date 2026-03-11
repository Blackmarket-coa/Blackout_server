from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

from twisted.web.resource import Resource

from synapse.api.errors import SynapseError
from synapse.http.server import DirectServeJsonResource
from synapse.http.site import SynapseRequest
from synapse.types import JsonDict, StateMap

from .server_semantics import (
    BLACKOUT_CHANNEL_TYPE_EVENT,
    GOVERNANCE_VOTE_EVENT,
    REPUTATION_UPDATE_EVENT,
    BlackoutPresenceService,
    BlackoutServerSemantics,
)

BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE = "m.blackout.presence"


@dataclass
class GovernanceDecision:
    token: int
    room_id: str
    event_id: str
    proposal_id: str
    decision: str
    finalized_at: int | None


class GovernanceDecisionStore:
    def __init__(self) -> None:
        self._next_token = 1
        self._decisions: List[GovernanceDecision] = []

    def ingest_event(self, event: Any) -> None:
        if event.type != GOVERNANCE_VOTE_EVENT:
            return

        content = event.content
        if not isinstance(content, Mapping):
            return

        proposal_id = content.get("proposal_id")
        decision = content.get("decision") or content.get("result") or content.get(
            "outcome"
        )
        if not isinstance(proposal_id, str) or not proposal_id:
            return
        if not isinstance(decision, str) or not decision:
            return

        self._decisions.append(
            GovernanceDecision(
                token=self._next_token,
                room_id=event.room_id,
                event_id=event.event_id,
                proposal_id=proposal_id,
                decision=decision,
                finalized_at=getattr(event, "origin_server_ts", None),
            )
        )
        self._next_token += 1

    def query(self, *, room_id: str, since: int) -> tuple[int, List[JsonDict]]:
        results = [
            {
                "token": d.token,
                "room_id": d.room_id,
                "event_id": d.event_id,
                "proposal_id": d.proposal_id,
                "decision": d.decision,
                "finalized_at": d.finalized_at,
            }
            for d in self._decisions
            if d.room_id == room_id and d.token > since
        ]
        return self._next_token - 1, results


class ReputationStore:
    def __init__(self) -> None:
        self._stats: Dict[str, Dict[str, object]] = {}
        self._cache: Dict[str, Dict[str, object]] = {}
        self._last_cache_ms: Dict[str, int] = {}
        self._cache_ttl_ms = 30_000

    def ingest_event(self, event: Any) -> None:
        if event.type != REPUTATION_UPDATE_EVENT:
            return

        content = event.content
        if not isinstance(content, Mapping):
            return

        node_id = content.get("node_id")
        delta = content.get("delta")
        reason = content.get("reason")

        if not isinstance(node_id, str) or not node_id:
            return
        if not isinstance(delta, (int, float)):
            return
        if not isinstance(reason, str) or not reason:
            return

        current = self._stats.setdefault(
            node_id,
            {
                "node_id": node_id,
                "events": 0,
                "total_delta": 0.0,
                "delivery_success_count": 0,
                "delivery_event_count": 0,
                "rating_sum": 0.0,
                "rating_count": 0,
                "attestation_status": "unknown",
                "governance_standing": "unknown",
            },
        )

        current["events"] = int(current["events"]) + 1
        current["total_delta"] = float(current["total_delta"]) + float(delta)

        if reason.startswith("delivery"):
            current["delivery_event_count"] = int(current["delivery_event_count"]) + 1
            if float(delta) > 0:
                current["delivery_success_count"] = int(current["delivery_success_count"]) + 1

        rating = content.get("rating")
        if isinstance(rating, (int, float)):
            current["rating_sum"] = float(current["rating_sum"]) + float(rating)
            current["rating_count"] = int(current["rating_count"]) + 1

        attestation_status = content.get("attestation_status")
        if isinstance(attestation_status, str) and attestation_status:
            current["attestation_status"] = attestation_status

        governance_standing = content.get("governance_standing")
        if isinstance(governance_standing, str) and governance_standing:
            current["governance_standing"] = governance_standing

        self._cache.pop(node_id, None)
        self._last_cache_ms.pop(node_id, None)

    def get(self, node_id: str) -> JsonDict:
        now_ms = int(time.time() * 1000)
        cached = self._cache.get(node_id)
        last_ms = self._last_cache_ms.get(node_id)
        if cached is not None and last_ms is not None and now_ms - last_ms < self._cache_ttl_ms:
            return dict(cached)

        current = self._stats.get(node_id)
        if current is None:
            result: JsonDict = {
                "node_id": node_id,
                "events": 0,
                "score": 0.0,
                "delivery_success_rate": None,
                "average_rating": None,
                "attestation_status": "unknown",
                "governance_standing": "unknown",
                "computed_at": now_ms,
                "cache_ttl_ms": self._cache_ttl_ms,
            }
        else:
            delivery_events = int(current["delivery_event_count"])
            delivery_success = int(current["delivery_success_count"])
            rating_count = int(current["rating_count"])
            rating_sum = float(current["rating_sum"])
            result = {
                "node_id": node_id,
                "events": int(current["events"]),
                "score": round(float(current["total_delta"]), 4),
                "delivery_success_rate": (
                    delivery_success / delivery_events if delivery_events > 0 else None
                ),
                "average_rating": (
                    rating_sum / rating_count if rating_count > 0 else None
                ),
                "attestation_status": str(current["attestation_status"]),
                "governance_standing": str(current["governance_standing"]),
                "computed_at": now_ms,
                "cache_ttl_ms": self._cache_ttl_ms,
            }

        self._cache[node_id] = dict(result)
        self._last_cache_ms[node_id] = now_ms
        return result


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

        body = _parse_json_body(request)
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


class GovernanceDecisionsResource(DirectServeJsonResource):
    def __init__(self, module_api: Any, decisions: GovernanceDecisionStore):
        super().__init__()
        self._module_api = module_api
        self._decisions = decisions

    async def _async_render_GET(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        await self._module_api.get_user_by_req(request)

        room_id = _parse_query_arg(request, "room_id", required=True)
        since_raw = _parse_query_arg(request, "since", required=False) or "0"

        try:
            since = int(since_raw)
        except ValueError as exc:
            raise SynapseError(400, "since must be an integer") from exc

        next_since, decisions = self._decisions.query(room_id=room_id, since=since)
        return 200, {
            "room_id": room_id,
            "since": since,
            "next_since": next_since,
            "decisions": decisions,
        }


class NodeReputationResource(DirectServeJsonResource):
    def __init__(self, module_api: Any, reputation: ReputationStore, node_id: str):
        super().__init__()
        self._module_api = module_api
        self._reputation = reputation
        self._node_id = node_id

    async def _async_render_GET(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        await self._module_api.get_user_by_req(request)
        return 200, self._reputation.get(self._node_id)


class ReputationRootResource(Resource):
    isLeaf = False

    def __init__(self, module_api: Any, reputation: ReputationStore):
        super().__init__()
        self._module_api = module_api
        self._reputation = reputation

    def getChild(self, path: bytes, request: SynapseRequest) -> Resource:
        del request
        if not path:
            return self
        return NodeReputationResource(
            self._module_api,
            self._reputation,
            path.decode("utf-8"),
        )


class BlackoutRootResource(Resource):
    isLeaf = False

    def __init__(
        self,
        module_api: Any,
        presence: BlackoutPresenceService,
        decisions: GovernanceDecisionStore,
        reputation: ReputationStore,
    ):
        super().__init__()
        self.putChild(b"presence", BlackoutPresenceResource(module_api, presence))
        governance_resource = Resource()
        governance_resource.putChild(
            b"decisions", GovernanceDecisionsResource(module_api, decisions)
        )
        self.putChild(b"governance", governance_resource)
        self.putChild(b"reputation", ReputationRootResource(module_api, reputation))


class BlackoutRuntimeModule:
    """Synapse module integration for blackout runtime semantics."""

    def __init__(self, config: JsonDict, module_api: Any):
        self._config = config
        self._module_api = module_api
        self._semantics = BlackoutServerSemantics()
        self._presence = BlackoutPresenceService()
        self._decisions = GovernanceDecisionStore()
        self._reputation = ReputationStore()

        self._module_api.register_third_party_rules_callbacks(
            on_create_room=self.on_create_room,
            check_event_allowed=self.check_event_allowed,
            on_new_event=self.on_new_event,
        )
        self._module_api.register_web_resource(
            "/_synapse/client/blackout",
            BlackoutRootResource(
                self._module_api,
                self._presence,
                self._decisions,
                self._reputation,
            ),
        )

    async def on_create_room(
        self,
        requester: Any,
        config: MutableMapping[str, object],
        is_requester_admin: bool,
    ) -> None:
        del is_requester_admin
        try:
            self._semantics.on_create_room(config)
        except ValueError as exc:
            raise SynapseError(403, str(exc))

        initial_state = config.get("initial_state")
        if not isinstance(initial_state, list):
            return

        requester_user_id = requester.user.to_string()
        for state_event in initial_state:
            if state_event.get("type") != "m.room.power_levels":
                continue

            content = state_event.get("content")
            if not isinstance(content, dict):
                continue

            users = content.get("users")
            if not isinstance(users, dict):
                users = {}
            users[requester_user_id] = max(int(users.get(requester_user_id, 0)), 100)
            content["users"] = users
            return

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

    async def on_new_event(self, event: Any, state_events: StateMap[Any]) -> None:
        del state_events
        self._decisions.ingest_event(event)
        self._reputation.ingest_event(event)

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


def _parse_json_body(request: SynapseRequest) -> JsonDict:
    raw = request.content.read()
    if not raw:
        raise SynapseError(400, "Request body must be JSON")

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SynapseError(400, "Malformed JSON in request body") from exc

    if not isinstance(body, dict):
        raise SynapseError(400, "Request body must be a JSON object")

    return body


def _parse_query_arg(request: SynapseRequest, key: str, *, required: bool) -> str | None:
    args = request.args or {}
    values = args.get(key.encode("utf-8"), [])
    if not values:
        if required:
            raise SynapseError(400, f"Missing required query parameter: {key}")
        return None

    try:
        return values[0].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SynapseError(400, f"Query parameter {key} must be utf-8") from exc
