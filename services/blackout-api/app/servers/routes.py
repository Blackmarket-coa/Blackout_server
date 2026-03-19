import secrets
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app import config
from app.auth.dependencies import CurrentUser, get_current_user
from app.db.connection import get_pool
from app.matrix.client import MatrixClient, MatrixError

router = APIRouter()
matrix = MatrixClient(config.SYNAPSE_URL, config.SYNAPSE_ADMIN_TOKEN)

ROLE_POWER_LEVELS = {"owner": 100, "admin": 50, "moderator": 25, "member": 0}


class CreateServerRequest(BaseModel):
    name: str
    icon_url: str | None = None


class JoinServerRequest(BaseModel):
    invite_code: str


class UpdateServerRequest(BaseModel):
    name: str | None = None
    icon_url: str | None = None


class UpdateRoleRequest(BaseModel):
    role: str


@router.post("")
async def create_server(body: CreateServerRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()

    # Create Matrix Space
    try:
        space = await matrix.create_space(user.matrix_access_token, body.name)
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    server_id = str(uuid.uuid4())
    invite_code = secrets.token_urlsafe(8)
    now = int(time.time() * 1000)

    # Create default #general channel
    try:
        room = await matrix.create_room(user.matrix_access_token, "general", space["room_id"])
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    channel_id = str(uuid.uuid4())

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO blackout_servers (id, name, icon_url, owner_user_id, matrix_space_id, invite_code, created_at) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                server_id, body.name, body.icon_url, user.id, space["room_id"], invite_code, now,
            )
            await conn.execute(
                "INSERT INTO blackout_channels (id, server_id, name, topic, channel_type, position, matrix_room_id, created_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
                channel_id, server_id, "general", "", "text", 0, room["room_id"], now,
            )
            await conn.execute(
                "INSERT INTO blackout_server_members (server_id, user_id, role, joined_at) VALUES ($1,$2,$3,$4)",
                server_id, user.id, "owner", now,
            )

    return {
        "id": server_id,
        "name": body.name,
        "icon_url": body.icon_url,
        "invite_code": invite_code,
        "channels": [{"id": channel_id, "name": "general", "type": "text", "topic": "", "position": 0}],
    }


@router.get("")
async def list_servers(user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.id, s.name, s.icon_url, sm.role
            FROM blackout_servers s
            JOIN blackout_server_members sm ON sm.server_id = s.id
            WHERE sm.user_id = $1
            ORDER BY s.created_at
        """, user.id)
    return [{"id": r["id"], "name": r["name"], "icon_url": r["icon_url"], "role": r["role"]} for r in rows]


@router.get("/{server_id}")
async def get_server(server_id: str, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        server = await conn.fetchrow("""
            SELECT s.id, s.name, s.icon_url, s.invite_code, sm.role
            FROM blackout_servers s
            JOIN blackout_server_members sm ON sm.server_id = s.id
            WHERE s.id = $1 AND sm.user_id = $2
        """, server_id, user.id)
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

        channels = await conn.fetch(
            "SELECT id, name, topic, channel_type, position FROM blackout_channels WHERE server_id = $1 ORDER BY position",
            server_id,
        )
        members = await conn.fetch("""
            SELECT u.id, u.username, u.display_name, u.avatar_url, sm.role
            FROM blackout_server_members sm
            JOIN blackout_users u ON u.id = sm.user_id
            WHERE sm.server_id = $1
        """, server_id)

    return {
        "id": server["id"],
        "name": server["name"],
        "icon_url": server["icon_url"],
        "invite_code": server["invite_code"],
        "role": server["role"],
        "channels": [{"id": c["id"], "name": c["name"], "topic": c["topic"], "type": c["channel_type"], "position": c["position"]} for c in channels],
        "members": [{"id": m["id"], "username": m["username"], "display_name": m["display_name"], "avatar_url": m["avatar_url"], "role": m["role"]} for m in members],
    }


@router.get("/{server_id}/members")
async def list_members(server_id: str, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        membership = await conn.fetchrow("SELECT 1 FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

        members = await conn.fetch("""
            SELECT u.id, u.username, u.display_name, u.avatar_url, sm.role
            FROM blackout_server_members sm
            JOIN blackout_users u ON u.id = sm.user_id
            WHERE sm.server_id = $1
        """, server_id)

    return [{"id": m["id"], "username": m["username"], "display_name": m["display_name"], "avatar_url": m["avatar_url"], "role": m["role"]} for m in members]


@router.patch("/{server_id}")
async def update_server(server_id: str, body: UpdateServerRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        membership = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not membership or membership["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can update server settings")

        server = await conn.fetchrow("SELECT id, name, icon_url, matrix_space_id FROM blackout_servers WHERE id = $1", server_id)
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

        new_name = body.name if body.name is not None else server["name"]
        new_icon = body.icon_url if body.icon_url is not None else server["icon_url"]

        await conn.execute("UPDATE blackout_servers SET name = $1, icon_url = $2 WHERE id = $3", new_name, new_icon, server_id)

    # Sync name change to Matrix Space
    if body.name is not None and body.name != server["name"]:
        try:
            await matrix.set_room_name(user.matrix_access_token, server["matrix_space_id"], body.name)
        except MatrixError:
            pass  # DB is source of truth; Matrix sync is best-effort

    return {"id": server_id, "name": new_name, "icon_url": new_icon}


@router.delete("/{server_id}")
async def delete_server(server_id: str, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        membership = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not membership or membership["role"] != "owner":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the server owner can delete a server")

        await conn.execute("DELETE FROM blackout_servers WHERE id = $1", server_id)

    return {"deleted": True}


@router.post("/{server_id}/join")
async def join_server(server_id: str, body: JoinServerRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        server = await conn.fetchrow("SELECT id, matrix_space_id, invite_code FROM blackout_servers WHERE id = $1", server_id)

    if not server or server["invite_code"] != body.invite_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid server or invite code")

    # Join Matrix Space + child rooms
    try:
        await matrix.join_room(user.matrix_access_token, server["matrix_space_id"])
    except MatrixError:
        pass  # May already be joined

    async with pool.acquire() as conn:
        channels = await conn.fetch("SELECT matrix_room_id FROM blackout_channels WHERE server_id = $1", server_id)

    for ch in channels:
        try:
            await matrix.join_room(user.matrix_access_token, ch["matrix_room_id"])
        except MatrixError:
            pass

    now = int(time.time() * 1000)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO blackout_server_members (server_id, user_id, role, joined_at) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
            server_id, user.id, "member", now,
        )

    return {"joined": True}


@router.delete("/{server_id}/leave")
async def leave_server(server_id: str, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        membership = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a member")
        if membership["role"] == "owner":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot leave. Transfer ownership first.")

        await conn.execute("DELETE FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)

    return {"left": True}


@router.put("/{server_id}/members/{member_id}/role")
async def update_member_role(server_id: str, member_id: str, body: UpdateRoleRequest, user: CurrentUser = Depends(get_current_user)):
    new_role = body.role
    if new_role not in ("admin", "moderator", "member"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be admin, moderator, or member")

    pool = get_pool()
    async with pool.acquire() as conn:
        caller = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not caller or caller["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can change roles")

        target = await conn.fetchrow(
            "SELECT u.matrix_user_id FROM blackout_server_members sm JOIN blackout_users u ON u.id = sm.user_id WHERE sm.server_id = $1 AND sm.user_id = $2",
            server_id, member_id,
        )
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        await conn.execute("UPDATE blackout_server_members SET role = $1 WHERE server_id = $2 AND user_id = $3", new_role, server_id, member_id)

    # Update Matrix power levels in all server rooms
    async with pool.acquire() as conn:
        channels = await conn.fetch("SELECT matrix_room_id FROM blackout_channels WHERE server_id = $1", server_id)

    power_level = ROLE_POWER_LEVELS[new_role]
    for ch in channels:
        try:
            await matrix.set_power_level(user.matrix_access_token, ch["matrix_room_id"], target["matrix_user_id"], power_level)
        except MatrixError:
            pass

    return {"updated": True}
