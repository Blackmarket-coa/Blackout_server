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


class CreateChannelRequest(BaseModel):
    name: str
    channel_type: str = "text"
    topic: str = ""


@router.post("/{server_id}/channels")
async def create_channel(server_id: str, body: CreateChannelRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        server = await conn.fetchrow("SELECT matrix_space_id FROM blackout_servers WHERE id = $1", server_id)
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")

        membership = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", server_id, user.id)
        if not membership or membership["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can create channels")

        max_pos = await conn.fetchval("SELECT COALESCE(MAX(position), -1) FROM blackout_channels WHERE server_id = $1", server_id)

    try:
        room = await matrix.create_room(user.matrix_access_token, body.name, server["matrix_space_id"], body.topic)
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    channel_id = str(uuid.uuid4())
    now = int(time.time() * 1000)
    position = max_pos + 1

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO blackout_channels (id, server_id, name, topic, channel_type, position, matrix_room_id, created_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
            channel_id, server_id, body.name, body.topic, body.channel_type, position, room["room_id"], now,
        )

    return {"id": channel_id, "name": body.name, "type": body.channel_type, "topic": body.topic, "position": position}


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        channel = await conn.fetchrow("SELECT id, server_id FROM blackout_channels WHERE id = $1", channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

        membership = await conn.fetchrow("SELECT role FROM blackout_server_members WHERE server_id = $1 AND user_id = $2", channel["server_id"], user.id)
        if not membership or membership["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or admin can delete channels")

        await conn.execute("DELETE FROM blackout_channels WHERE id = $1", channel_id)

    return {"deleted": True}
