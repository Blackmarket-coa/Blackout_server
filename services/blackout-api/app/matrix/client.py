"""Thin HTTP client for Synapse Client-Server and Admin APIs."""

import hmac
import hashlib

import httpx


class MatrixError(Exception):
    def __init__(self, status: int, errcode: str, error: str):
        super().__init__(error)
        self.status = status
        self.errcode = errcode


class MatrixClient:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url.rstrip("/")
        self.admin_token = admin_token

    def _client(self, access_token: str | None = None) -> httpx.AsyncClient:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=30.0)

    async def _request(self, method: str, path: str, access_token: str | None = None, **kwargs) -> dict:
        async with self._client(access_token) as client:
            resp = await client.request(method, path, **kwargs)
            if resp.status_code >= 400:
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                raise MatrixError(resp.status_code, body.get("errcode", "M_UNKNOWN"), body.get("error", resp.text))
            return resp.json()

    # --- Auth ---

    async def register_user(self, username: str, password: str, shared_secret: str, admin: bool = False) -> dict:
        """Register a user via Synapse shared-secret registration."""
        nonce_resp = await self._request("GET", "/_synapse/admin/v1/register")
        nonce = nonce_resp["nonce"]

        mac_msg = f"{nonce}\x00{username}\x00{password}\x00{'admin' if admin else 'notadmin'}"
        mac = hmac.new(shared_secret.encode(), mac_msg.encode(), hashlib.sha1).hexdigest()

        return await self._request("POST", "/_synapse/admin/v1/register", json={
            "nonce": nonce,
            "username": username,
            "password": password,
            "admin": admin,
            "mac": mac,
        })

    async def login(self, username: str, password: str) -> dict:
        """Login via Matrix password auth. Returns access_token + user_id."""
        return await self._request("POST", "/_matrix/client/v3/login", json={
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": username},
            "password": password,
        })

    # --- Rooms / Spaces ---

    async def create_space(self, access_token: str, name: str, topic: str = "") -> dict:
        """Create a Matrix Space (room with type m.space)."""
        return await self._request("POST", "/_matrix/client/v3/createRoom", access_token=access_token, json={
            "name": name,
            "topic": topic,
            "creation_content": {"type": "m.space"},
            "visibility": "private",
            "preset": "private_chat",
            "power_level_content_override": {
                "users_default": 0,
                "events_default": 0,
                "invite": 50,
            },
        })

    async def create_room(self, access_token: str, name: str, space_id: str, topic: str = "") -> dict:
        """Create a room as a child of a Space."""
        room = await self._request("POST", "/_matrix/client/v3/createRoom", access_token=access_token, json={
            "name": name,
            "topic": topic,
            "visibility": "private",
            "preset": "private_chat",
        })
        room_id = room["room_id"]

        # Add as child of space
        await self._request(
            "PUT",
            f"/_matrix/client/v3/rooms/{space_id}/state/m.space.child/{room_id}",
            access_token=access_token,
            json={"via": [], "suggested": True},
        )
        return room

    async def join_room(self, access_token: str, room_id: str) -> dict:
        return await self._request("POST", f"/_matrix/client/v3/join/{room_id}", access_token=access_token, json={})

    async def invite_user(self, access_token: str, room_id: str, user_id: str) -> dict:
        return await self._request("POST", f"/_matrix/client/v3/rooms/{room_id}/invite", access_token=access_token, json={
            "user_id": user_id,
        })

    async def get_room_messages(self, access_token: str, room_id: str, limit: int = 50, from_token: str | None = None) -> dict:
        params: dict = {"dir": "b", "limit": str(limit)}
        if from_token:
            params["from"] = from_token
        return await self._request("GET", f"/_matrix/client/v3/rooms/{room_id}/messages", access_token=access_token, params=params)

    async def send_message(self, access_token: str, room_id: str, body: str, txn_id: str) -> dict:
        return await self._request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn_id}",
            access_token=access_token,
            json={"msgtype": "m.text", "body": body},
        )

    async def set_power_level(self, access_token: str, room_id: str, user_id: str, level: int) -> None:
        """Set a user's power level in a room."""
        state = await self._request("GET", f"/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels", access_token=access_token)
        state.setdefault("users", {})[user_id] = level
        await self._request("PUT", f"/_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels", access_token=access_token, json=state)

    async def get_space_children(self, access_token: str, space_id: str) -> list[str]:
        """Get child room IDs of a space."""
        state = await self._request("GET", f"/_matrix/client/v3/rooms/{space_id}/state", access_token=access_token)
        return [
            event["state_key"]
            for event in state
            if event.get("type") == "m.space.child" and event.get("content", {}).get("via") is not None
        ]

    async def whoami(self, access_token: str) -> dict:
        return await self._request("GET", "/_matrix/client/v3/account/whoami", access_token=access_token)
