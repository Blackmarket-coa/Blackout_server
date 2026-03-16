from __future__ import annotations

import json
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, List, Mapping, MutableMapping, Optional, Set, Tuple

from twisted.web.resource import Resource

from synapse.api.errors import SynapseError
from synapse.http.server import DirectServeJsonResource
from synapse.http.site import SynapseRequest
from synapse.types import JsonDict, StateMap

from .server_semantics import (
    BLACKOUT_CHANNEL_TYPE_EVENT,
    GOVERNANCE_PROPOSAL_EVENT,
    GOVERNANCE_VOTE_EVENT,
    REPUTATION_UPDATE_EVENT,
    ANNOUNCEMENT_POLICY_EVENT,
    BlackoutPresenceService,
    BlackoutServerSemantics,
)

BLACKOUT_PRESENCE_ACCOUNT_DATA_TYPE = "m.blackout.presence"
DEAD_DROP_CHANNEL_TYPE = "blackout_dead_drop_room"
ANNOUNCEMENT_CHANNEL_TYPE = "blackout_announcement_room"
DEAD_DROP_MESSAGE_EVENT_TYPE = "m.room.message"
ANNOUNCEMENT_MESSAGE_EVENT_TYPE = "m.room.message"



@dataclass
class GovernanceDecision:
    token: int
    room_id: str
    event_id: str
    proposal_id: str
    decision: str
    finalized_at: int | None


class GovernanceDecisionStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._next_token = 1
        self._decisions: List[GovernanceDecision] = []
        self._seen_event_ids: Set[str] = set()
        self._voter_registry: Set[Tuple[str, str, str]] = set()
        self._load()

    def _load(self) -> None:
        rows = self._conn.execute(
            "SELECT token, room_id, event_id, proposal_id, decision, finalized_at, sender FROM blackout_governance_decisions ORDER BY token ASC"
        ).fetchall()
        for token, room_id, event_id, proposal_id, decision, finalized_at, sender in rows:
            self._decisions.append(
                GovernanceDecision(token, room_id, event_id, proposal_id, decision, finalized_at)
            )
            self._seen_event_ids.add(event_id)
            self._voter_registry.add((room_id, proposal_id, sender))

        if self._decisions:
            self._next_token = self._decisions[-1].token + 1

    def has_voted(self, room_id: str, proposal_id: str, sender: str) -> bool:
        return (room_id, proposal_id, sender) in self._voter_registry

    def ingest_event(self, event: Any) -> bool:
        if event.type != GOVERNANCE_VOTE_EVENT or event.event_id in self._seen_event_ids:
            return False

        content = event.content
        if not isinstance(content, Mapping):
            return False

        proposal_id = content.get("proposal_id")
        decision = content.get("decision") or content.get("result") or content.get("outcome")
        sender = getattr(event, "sender", "")
        if not isinstance(proposal_id, str) or not proposal_id:
            return False
        if not isinstance(sender, str) or not sender:
            return False

        self._voter_registry.add((event.room_id, proposal_id, sender))

        if not isinstance(decision, str) or not decision:
            self._seen_event_ids.add(event.event_id)
            return False

        record = GovernanceDecision(
            token=self._next_token,
            room_id=event.room_id,
            event_id=event.event_id,
            proposal_id=proposal_id,
            decision=decision,
            finalized_at=getattr(event, "origin_server_ts", None),
        )
        self._decisions.append(record)
        self._seen_event_ids.add(event.event_id)
        self._next_token += 1

        self._conn.execute(
            "INSERT OR IGNORE INTO blackout_governance_decisions (token, room_id, event_id, proposal_id, decision, finalized_at, sender) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                record.token,
                record.room_id,
                record.event_id,
                record.proposal_id,
                record.decision,
                record.finalized_at,
                sender,
            ),
        )
        self._conn.commit()
        return True

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
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._stats: Dict[str, Dict[str, object]] = {}
        self._cache: Dict[str, Dict[str, object]] = {}
        self._last_cache_ms: Dict[str, int] = {}
        self._cache_ttl_ms = 30_000
        self._seen_event_ids: Set[str] = set()
        self._load()

    def _load(self) -> None:
        rows = self._conn.execute(
            "SELECT event_id, node_id, delta, reason, rating, attestation_status, governance_standing FROM blackout_reputation_updates ORDER BY rowid ASC"
        ).fetchall()
        for row in rows:
            event_id, node_id, delta, reason, rating, attestation_status, governance_standing = row
            self._seen_event_ids.add(event_id)
            self._apply(
                {
                    "event_id": event_id,
                    "content": {
                        "node_id": node_id,
                        "delta": delta,
                        "reason": reason,
                        "rating": rating,
                        "attestation_status": attestation_status,
                        "governance_standing": governance_standing,
                    },
                }
            )

    def _apply(self, event: Mapping[str, object]) -> bool:
        content = event.get("content")
        if not isinstance(content, Mapping):
            return False
        node_id = content.get("node_id")
        delta = content.get("delta")
        reason = content.get("reason")
        if not isinstance(node_id, str) or not node_id:
            return False
        if not isinstance(delta, (int, float)):
            return False
        if not isinstance(reason, str) or not reason:
            return False

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
        return True

    def ingest_event(self, event: Any) -> bool:
        if event.type != REPUTATION_UPDATE_EVENT or event.event_id in self._seen_event_ids:
            return False
        if not self._apply({"content": event.content}):
            return False

        content = event.content
        self._conn.execute(
            "INSERT OR IGNORE INTO blackout_reputation_updates (event_id, node_id, delta, reason, rating, attestation_status, governance_standing) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                event.event_id,
                content.get("node_id"),
                float(content.get("delta")),
                content.get("reason"),
                content.get("rating") if isinstance(content.get("rating"), (int, float)) else None,
                content.get("attestation_status") if isinstance(content.get("attestation_status"), str) else None,
                content.get("governance_standing") if isinstance(content.get("governance_standing"), str) else None,
            ),
        )
        self._conn.commit()
        self._seen_event_ids.add(event.event_id)
        return True

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
                "delivery_success_rate": delivery_success / delivery_events if delivery_events else None,
                "average_rating": rating_sum / rating_count if rating_count else None,
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
    def __init__(self, module_api: Any, module: "BlackoutRuntimeModule"):
        super().__init__()
        self._module_api = module_api
        self._module = module

    async def _async_render_GET(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        await self._module_api.get_user_by_req(request)

        room_id = _parse_query_arg(request, "room_id", required=True)
        since_raw = _parse_query_arg(request, "since", required=False) or "0"

        try:
            since = int(since_raw)
        except ValueError as exc:
            raise SynapseError(400, "since must be an integer") from exc

        await self._module.backfill_room(room_id)
        next_since, decisions = self._module._decisions.query(room_id=room_id, since=since)
        return 200, {
            "room_id": room_id,
            "since": since,
            "next_since": next_since,
            "decisions": decisions,
        }


class NodeReputationResource(DirectServeJsonResource):
    def __init__(self, module_api: Any, module: "BlackoutRuntimeModule", node_id: str):
        super().__init__()
        self._module_api = module_api
        self._module = module
        self._node_id = node_id

    async def _async_render_GET(self, request: SynapseRequest) -> tuple[int, JsonDict]:
        await self._module_api.get_user_by_req(request)
        await self._module.backfill_node(self._node_id)
        return 200, self._module._reputation.get(self._node_id)


class ReputationRootResource(Resource):
    isLeaf = False

    def __init__(self, module_api: Any, module: "BlackoutRuntimeModule"):
        super().__init__()
        self._module_api = module_api
        self._module = module

    def getChild(self, path: bytes, request: SynapseRequest) -> Resource:
        del request
        if not path:
            return self
        return NodeReputationResource(self._module_api, self._module, path.decode("utf-8"))


class BlackoutRootResource(Resource):
    isLeaf = False

    def __init__(self, module_api: Any, module: "BlackoutRuntimeModule"):
        super().__init__()
        self.putChild(b"presence", BlackoutPresenceResource(module_api, module._presence))
        governance_resource = Resource()
        governance_resource.putChild(b"decisions", GovernanceDecisionsResource(module_api, module))
        self.putChild(b"governance", governance_resource)
        self.putChild(b"reputation", ReputationRootResource(module_api, module))


class BlackoutRuntimeModule:
    """Synapse module integration for blackout runtime semantics."""

    def __init__(self, config: JsonDict, module_api: Any):
        self._config = config
        self._module_api = module_api
        self._store = module_api._store
        self._semantics = BlackoutServerSemantics()
        self._presence = BlackoutPresenceService()
        self._proposal_rate_window_s = int(config.get("proposal_rate_window_s", 3600))
        self._proposal_rate_limit = int(config.get("proposal_rate_limit", 5))
        self._attestation_cooldown_s = int(config.get("attestation_cooldown_s", 600))
        self._proposal_times: Dict[str, Deque[int]] = defaultdict(deque)
        self._attestation_times: Dict[Tuple[str, str], int] = {}
        self._backfilled_rooms: Set[str] = set()
        self._backfilled_nodes: Set[str] = set()
        self._dead_drop_ttl_hours = int(config.get("dead_drop_ttl_hours", 24))
        self._dead_drop_purge_batch_size = int(config.get("dead_drop_purge_batch_size", 100))

        db_path = Path(str(config.get("persistence_path", "/tmp/blackout_runtime.sqlite3")))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS blackout_governance_decisions (token INTEGER PRIMARY KEY, room_id TEXT NOT NULL, event_id TEXT NOT NULL UNIQUE, proposal_id TEXT NOT NULL, decision TEXT NOT NULL, finalized_at INTEGER, sender TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS blackout_reputation_updates (event_id TEXT PRIMARY KEY, node_id TEXT NOT NULL, delta REAL NOT NULL, reason TEXT NOT NULL, rating REAL, attestation_status TEXT, governance_standing TEXT)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS blackout_dead_drop_retention (event_id TEXT PRIMARY KEY, room_id TEXT NOT NULL, expires_at_ms INTEGER NOT NULL, purged_at_ms INTEGER)"
        )
        self._conn.commit()

        self._decisions = GovernanceDecisionStore(self._conn)
        self._reputation = ReputationStore(self._conn)

        self._module_api.register_third_party_rules_callbacks(
            on_create_room=self.on_create_room,
            check_event_allowed=self.check_event_allowed,
            on_new_event=self.on_new_event,
        )
        self._module_api.register_web_resource("/_synapse/client/blackout", BlackoutRootResource(self._module_api, self))

    async def backfill_room(self, room_id: str) -> None:
        if room_id in self._backfilled_rooms:
            return
        limit = int(self._config.get("backfill_room_limit", 1000))
        end_token = self._store.get_room_max_token()
        events, _ = await self._store.get_recent_events_for_room(room_id, limit, end_token)
        for event in events:
            self._decisions.ingest_event(event)
            self._reputation.ingest_event(event)
        self._backfilled_rooms.add(room_id)

    async def backfill_node(self, node_id: str) -> None:
        if node_id in self._backfilled_nodes:
            return

        like_pattern = f'%"node_id":"{node_id}"%'

        def _txn(txn: Any) -> List[str]:
            txn.execute(
                "SELECT event_id FROM event_json WHERE json LIKE ?",
                (like_pattern,),
            )
            return [row[0] for row in txn]

        event_ids = await self._store.db_pool.runInteraction("blackout_backfill_node", _txn)
        if event_ids:
            events = await self._store.get_events_as_list(event_ids)
            for event in events:
                self._reputation.ingest_event(event)
        self._backfilled_nodes.add(node_id)

    async def on_create_room(self, requester: Any, config: MutableMapping[str, object], is_requester_admin: bool) -> None:
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

    async def check_event_allowed(self, event: Any, state_events: StateMap[Any]) -> tuple[bool, Optional[dict]]:
        channel_type = self._extract_channel_type(state_events)

        try:
            self._semantics.check_event_allowed(event.type, event.content, channel_type=channel_type)
        except ValueError as exc:
            raise SynapseError(403, str(exc))

        now = int(time.time())
        sender = getattr(event, "sender", "")
        room_id = getattr(event, "room_id", "")

        if event.type == GOVERNANCE_PROPOSAL_EVENT and isinstance(sender, str):
            q = self._proposal_times[sender]
            while q and q[0] <= now - self._proposal_rate_window_s:
                q.popleft()
            if len(q) >= self._proposal_rate_limit:
                raise SynapseError(429, "Governance proposal rate limit exceeded")
            q.append(now)

        if event.type == GOVERNANCE_VOTE_EVENT:
            proposal_id = event.content.get("proposal_id") if isinstance(event.content, Mapping) else None
            if isinstance(proposal_id, str) and isinstance(sender, str) and isinstance(room_id, str):
                if self._decisions.has_voted(room_id, proposal_id, sender):
                    raise SynapseError(403, "Only one vote per user per proposal is allowed")

        if event.type == REPUTATION_UPDATE_EVENT and isinstance(event.content, Mapping):
            node_id = event.content.get("node_id")
            attestation_status = event.content.get("attestation_status")
            if isinstance(node_id, str) and isinstance(attestation_status, str) and isinstance(sender, str):
                key = (sender, node_id)
                last = self._attestation_times.get(key)
                if last is not None and now - last < self._attestation_cooldown_s:
                    raise SynapseError(429, "Attestation update cooldown active")
                self._attestation_times[key] = now

        if channel_type == ANNOUNCEMENT_CHANNEL_TYPE and event.type == ANNOUNCEMENT_MESSAGE_EVENT_TYPE:
            if not isinstance(sender, str) or not sender:
                raise SynapseError(403, "Announcement sender identity required")
            sender_power = self._sender_power_level(sender, state_events)
            required_power = self._required_event_power_level(event.type, state_events)
            if sender_power < required_power:
                raise SynapseError(403, "Sender is not permitted to post in announcement room")

            policy = self._announcement_policy(state_events)
            allowed_roles = policy.get("sender_roles")
            sender_role = event.content.get("blackout_sender_role") if isinstance(event.content, Mapping) else None
            if isinstance(allowed_roles, list):
                if not isinstance(sender_role, str) or sender_role not in allowed_roles:
                    raise SynapseError(403, "Sender role is not allowed for announcement fanout")

            fanout_mode = policy.get("fanout_mode", "immediate")
            if fanout_mode == "delayed_window":
                fanout = event.content.get("blackout_fanout") if isinstance(event.content, Mapping) else None
                if not isinstance(fanout, Mapping):
                    raise SynapseError(403, "Delayed fanout policy requires blackout_fanout payload")
                delay_ms = fanout.get("delay_ms")
                if not isinstance(delay_ms, int):
                    raise SynapseError(403, "Delayed fanout requires integer delay_ms")
                min_ms = policy.get("delayed_fanout_min_ms", 0)
                max_ms = policy.get("delayed_fanout_max_ms", 0)
                if not isinstance(min_ms, int) or not isinstance(max_ms, int) or delay_ms < min_ms or delay_ms > max_ms:
                    raise SynapseError(403, "Delayed fanout delay_ms is outside policy bounds")

        return True, None

    async def on_new_event(self, event: Any, state_events: StateMap[Any]) -> None:
        channel_type = self._extract_channel_type(state_events)
        if channel_type == DEAD_DROP_CHANNEL_TYPE and event.type == DEAD_DROP_MESSAGE_EVENT_TYPE:
            event_ts_ms = getattr(event, "origin_server_ts", None)
            if not isinstance(event_ts_ms, int):
                event_ts_ms = int(time.time() * 1000)
            expires_at_ms = event_ts_ms + (self._dead_drop_ttl_hours * 3_600_000)
            self._conn.execute(
                "INSERT OR IGNORE INTO blackout_dead_drop_retention (event_id, room_id, expires_at_ms, purged_at_ms) VALUES (?, ?, ?, NULL)",
                (event.event_id, event.room_id, expires_at_ms),
            )
            self._conn.commit()

        self._decisions.ingest_event(event)
        self._reputation.ingest_event(event)

    def run_dead_drop_purge(self, *, now_ms: Optional[int] = None) -> List[JsonDict]:
        if now_ms is None:
            now_ms = int(time.time() * 1000)

        rows = self._conn.execute(
            "SELECT event_id, room_id, expires_at_ms FROM blackout_dead_drop_retention WHERE purged_at_ms IS NULL AND expires_at_ms <= ? ORDER BY expires_at_ms ASC LIMIT ?",
            (now_ms, self._dead_drop_purge_batch_size),
        ).fetchall()

        purged: List[JsonDict] = []
        for event_id, room_id, expires_at_ms in rows:
            self._conn.execute(
                "UPDATE blackout_dead_drop_retention SET purged_at_ms = ? WHERE event_id = ?",
                (now_ms, event_id),
            )
            purged.append(
                {
                    "event_id": event_id,
                    "room_id": room_id,
                    "expires_at_ms": expires_at_ms,
                    "purged_at_ms": now_ms,
                    "tombstone_event_type": "m.room.tombstone",
                }
            )

        if rows:
            self._conn.commit()
        return purged

    def get_dead_drop_retention_record(self, event_id: str) -> Optional[JsonDict]:
        row = self._conn.execute(
            "SELECT event_id, room_id, expires_at_ms, purged_at_ms FROM blackout_dead_drop_retention WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "event_id": row[0],
            "room_id": row[1],
            "expires_at_ms": row[2],
            "purged_at_ms": row[3],
        }

    @staticmethod
    def _announcement_policy(state_events: StateMap[Any]) -> JsonDict:
        event = state_events.get((ANNOUNCEMENT_POLICY_EVENT, ""))
        content = getattr(event, "content", None)
        if isinstance(content, Mapping):
            return dict(content)
        return {
            "sender_roles": ["announcer", "moderator"],
            "fanout_mode": "immediate",
            "delayed_fanout_min_ms": 5_000,
            "delayed_fanout_max_ms": 30_000,
        }

    @staticmethod
    def _sender_power_level(sender: str, state_events: StateMap[Any]) -> int:
        event = state_events.get(("m.room.power_levels", ""))
        content = getattr(event, "content", None)
        if not isinstance(content, Mapping):
            return 0
        users = content.get("users")
        if isinstance(users, Mapping):
            level = users.get(sender)
            if isinstance(level, int):
                return level
        users_default = content.get("users_default")
        if isinstance(users_default, int):
            return users_default
        return 0

    @staticmethod
    def _required_event_power_level(event_type: str, state_events: StateMap[Any]) -> int:
        event = state_events.get(("m.room.power_levels", ""))
        content = getattr(event, "content", None)
        if not isinstance(content, Mapping):
            return 50
        events = content.get("events")
        if isinstance(events, Mapping):
            required = events.get(event_type)
            if isinstance(required, int):
                return required
        events_default = content.get("events_default")
        if isinstance(events_default, int):
            return events_default
        return 50

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
