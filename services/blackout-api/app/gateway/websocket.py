"""WebSocket gateway that relays Matrix /sync as Discord-style events.

Protocol:
1. Client connects to WS /gateway
2. Client sends: {"token": "jwt..."}
3. Server responds: {"type": "READY", "user_id": "..."}
4. Server long-polls Synapse /sync and relays transformed events:
   - MESSAGE_CREATE { channel_id, message: { id, content, author, timestamp } }
   - MESSAGE_DELETE { channel_id, message_id }
   - MEMBER_JOIN { server_id, user: { id, username } }
   - MEMBER_LEAVE { server_id, user_id }
   - TYPING_START { channel_id, user_ids }
5. Client can send:
   - {"type": "PING"} → server replies {"type": "PONG"}
6. Server sends {"type": "HEARTBEAT"} every 30s
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.jwt import decode_token
from app import config
from app.db.connection import get_pool
from app.matrix.client import MatrixClient, MatrixError

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 30  # seconds
SYNC_TIMEOUT = 30000  # milliseconds (server-side long-poll)


class RoomChannelCache:
    """Caches matrix_room_id → (channel_id, server_id) mappings."""

    def __init__(self):
        self._cache: dict[str, tuple[str, str]] = {}
        self._loaded = False

    async def load(self) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT matrix_room_id, id, server_id FROM blackout_channels"
            )
        self._cache = {r["matrix_room_id"]: (r["id"], r["server_id"]) for r in rows}
        self._loaded = True

    async def get(self, matrix_room_id: str) -> tuple[str, str] | None:
        """Returns (channel_id, server_id) or None if room isn't mapped."""
        if not self._loaded:
            await self.load()
        result = self._cache.get(matrix_room_id)
        if result is None:
            # Cache miss — try a fresh DB lookup (room may have been created recently)
            pool = get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, server_id FROM blackout_channels WHERE matrix_room_id = $1",
                    matrix_room_id,
                )
            if row:
                self._cache[matrix_room_id] = (row["id"], row["server_id"])
                return (row["id"], row["server_id"])
            return None
        return result

    def invalidate(self) -> None:
        self._cache.clear()
        self._loaded = False


class UserCache:
    """Caches matrix_user_id → {id, username, display_name}."""

    def __init__(self):
        self._cache: dict[str, dict] = {}

    async def resolve(self, matrix_user_id: str) -> dict:
        if matrix_user_id in self._cache:
            return self._cache[matrix_user_id]

        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, username, display_name, avatar_url FROM blackout_users WHERE matrix_user_id = $1",
                matrix_user_id,
            )
        if row:
            info = {
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "avatar_url": row["avatar_url"],
            }
        else:
            # Fallback for unmapped users (e.g., federated or bot accounts)
            info = {
                "id": matrix_user_id,
                "username": matrix_user_id.split(":")[0].lstrip("@"),
                "display_name": None,
                "avatar_url": None,
            }
        self._cache[matrix_user_id] = info
        return info


class SyncRelay:
    """Runs a /sync loop for one user, transforms events, sends over WebSocket."""

    def __init__(self, ws: WebSocket, access_token: str, user_id: str):
        self.ws = ws
        self.access_token = access_token
        self.user_id = user_id
        self.matrix = MatrixClient(config.SYNAPSE_URL, config.SYNAPSE_ADMIN_TOKEN)
        self.room_cache = RoomChannelCache()
        self.user_cache = UserCache()
        self.since_token: str | None = None
        self._running = False

    async def run(self) -> None:
        """Main sync loop. Runs until cancelled or WebSocket disconnects."""
        self._running = True

        # Do an initial sync with timeout=0 to get since_token without blocking
        try:
            initial = await self.matrix.sync(self.access_token, since=None, timeout=0)
            self.since_token = initial.get("next_batch")
        except MatrixError as e:
            logger.warning("Initial sync failed for user %s: %s", self.user_id, e)
            await self._send({"type": "ERROR", "detail": f"Sync initialization failed: {e}"})
            return

        while self._running:
            try:
                resp = await self.matrix.sync(
                    self.access_token,
                    since=self.since_token,
                    timeout=SYNC_TIMEOUT,
                )
                self.since_token = resp.get("next_batch", self.since_token)
                await self._process_sync(resp)
            except MatrixError as e:
                logger.warning("Sync error for user %s: %s", self.user_id, e)
                if e.status == 401:
                    await self._send({"type": "ERROR", "detail": "Matrix session expired"})
                    self._running = False
                    break
                # Backoff on other errors
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected sync error for user %s", self.user_id)
                await asyncio.sleep(5)

    def stop(self) -> None:
        self._running = False

    async def _send(self, event: dict) -> None:
        """Send a JSON event over the WebSocket."""
        try:
            await self.ws.send_json(event)
        except Exception:
            self._running = False

    async def _process_sync(self, sync_resp: dict) -> None:
        """Transform Matrix sync response into Discord-style events."""
        rooms = sync_resp.get("rooms", {})

        # Process joined rooms
        for room_id, room_data in rooms.get("join", {}).items():
            mapping = await self.room_cache.get(room_id)
            if not mapping:
                continue  # Not a Blackout-managed room
            channel_id, server_id = mapping

            # Timeline events (messages, redactions)
            for event in room_data.get("timeline", {}).get("events", []):
                await self._process_timeline_event(event, channel_id, server_id)

            # State events (membership changes)
            for event in room_data.get("state", {}).get("events", []):
                await self._process_state_event(event, channel_id, server_id)

            # Ephemeral events (typing)
            for event in room_data.get("ephemeral", {}).get("events", []):
                await self._process_ephemeral_event(event, channel_id)

        # Process rooms the user was invited to
        for room_id, room_data in rooms.get("invite", {}).items():
            mapping = await self.room_cache.get(room_id)
            if mapping:
                channel_id, server_id = mapping
                await self._send({
                    "type": "CHANNEL_INVITE",
                    "channel_id": channel_id,
                    "server_id": server_id,
                })

    async def _process_timeline_event(self, event: dict, channel_id: str, server_id: str) -> None:
        event_type = event.get("type")
        sender = event.get("sender", "")

        if event_type == "m.room.message":
            content = event.get("content", {})
            author = await self.user_cache.resolve(sender)
            await self._send({
                "type": "MESSAGE_CREATE",
                "channel_id": channel_id,
                "message": {
                    "id": event.get("event_id"),
                    "content": content.get("body", ""),
                    "author": author,
                    "timestamp": event.get("origin_server_ts"),
                },
            })

        elif event_type == "m.room.redaction":
            await self._send({
                "type": "MESSAGE_DELETE",
                "channel_id": channel_id,
                "message_id": event.get("redacts"),
            })

        elif event_type == "m.room.member":
            membership = event.get("content", {}).get("membership")
            user_matrix_id = event.get("state_key", sender)
            user_info = await self.user_cache.resolve(user_matrix_id)

            if membership == "join":
                prev = event.get("unsigned", {}).get("prev_content", {}).get("membership")
                if prev != "join":  # Only emit on actual join, not profile updates
                    await self._send({
                        "type": "MEMBER_JOIN",
                        "server_id": server_id,
                        "channel_id": channel_id,
                        "user": user_info,
                    })
            elif membership == "leave":
                await self._send({
                    "type": "MEMBER_LEAVE",
                    "server_id": server_id,
                    "channel_id": channel_id,
                    "user_id": user_info["id"],
                })

    async def _process_state_event(self, event: dict, channel_id: str, server_id: str) -> None:
        # State events in sync response — handle membership changes the same way
        if event.get("type") == "m.room.member":
            await self._process_timeline_event(event, channel_id, server_id)

    async def _process_ephemeral_event(self, event: dict, channel_id: str) -> None:
        if event.get("type") == "m.typing":
            typers = event.get("content", {}).get("user_ids", [])
            resolved = []
            for matrix_uid in typers:
                info = await self.user_cache.resolve(matrix_uid)
                resolved.append(info["id"])
            await self._send({
                "type": "TYPING_START",
                "channel_id": channel_id,
                "user_ids": resolved,
            })


@router.websocket("/gateway")
async def gateway(ws: WebSocket):
    await ws.accept()

    # --- Authentication ---
    try:
        auth_msg = await ws.receive_text()
        data = json.loads(auth_msg)
        token = data.get("token", "")
        payload = decode_token(token)
    except Exception:
        await ws.send_json({"type": "ERROR", "detail": "Authentication required. Send {\"token\": \"...\"}."})
        await ws.close(code=4001)
        return

    user_id = payload["sub"]
    matrix_access_token = payload["matrix_access_token"]

    await ws.send_json({
        "type": "READY",
        "user_id": user_id,
    })

    # --- Start sync relay + heartbeat ---
    relay = SyncRelay(ws, matrix_access_token, user_id)
    sync_task = asyncio.create_task(relay.run())
    heartbeat_task = asyncio.create_task(_heartbeat_loop(ws))

    try:
        # Listen for client messages while sync runs in background
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type == "PING":
                await ws.send_json({"type": "PONG"})
            elif msg_type == "RESUME":
                # Client can send a since_token to resume from a specific point
                since = data.get("since")
                if since:
                    relay.since_token = since
    except WebSocketDisconnect:
        pass
    finally:
        relay.stop()
        sync_task.cancel()
        heartbeat_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass


async def _heartbeat_loop(ws: WebSocket) -> None:
    """Send periodic heartbeats to keep the connection alive."""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await ws.send_json({"type": "HEARTBEAT"})
    except (asyncio.CancelledError, Exception):
        pass
