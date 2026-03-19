import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app import config
from app.auth.dependencies import CurrentUser, get_current_user
from app.db.connection import get_pool
from app.matrix.client import MatrixClient, MatrixError

router = APIRouter()
matrix = MatrixClient(config.SYNAPSE_URL, config.SYNAPSE_ADMIN_TOKEN)


class SendMessageRequest(BaseModel):
    content: str


@router.get("/{channel_id}/messages")
async def get_messages(
    channel_id: str,
    user: CurrentUser = Depends(get_current_user),
    limit: int = Query(default=50, le=100),
    before: str | None = Query(default=None),
):
    pool = get_pool()
    async with pool.acquire() as conn:
        channel = await conn.fetchrow("SELECT matrix_room_id, server_id FROM blackout_channels WHERE id = $1", channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    try:
        result = await matrix.get_room_messages(user.matrix_access_token, channel["matrix_room_id"], limit=limit, from_token=before)
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    # Resolve senders to clean usernames
    async with pool.acquire() as conn:
        user_rows = await conn.fetch("SELECT matrix_user_id, id, username, display_name, avatar_url FROM blackout_users")
    user_map = {r["matrix_user_id"]: r for r in user_rows}

    messages = []
    for event in result.get("chunk", []):
        if event.get("type") != "m.room.message":
            continue
        sender_matrix = event.get("sender", "")
        sender_info = user_map.get(sender_matrix)
        messages.append({
            "id": event.get("event_id"),
            "content": event.get("content", {}).get("body", ""),
            "author": {
                "id": sender_info["id"] if sender_info else sender_matrix,
                "username": sender_info["username"] if sender_info else sender_matrix.split(":")[0].lstrip("@"),
                "display_name": sender_info["display_name"] if sender_info else None,
                "avatar_url": sender_info["avatar_url"] if sender_info else None,
            },
            "timestamp": event.get("origin_server_ts"),
        })

    return {
        "messages": messages,
        "next_cursor": result.get("end"),
    }


@router.post("/{channel_id}/messages")
async def send_message(channel_id: str, body: SendMessageRequest, user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        channel = await conn.fetchrow("SELECT matrix_room_id FROM blackout_channels WHERE id = $1", channel_id)
        if not channel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    txn_id = str(uuid.uuid4())
    try:
        result = await matrix.send_message(user.matrix_access_token, channel["matrix_room_id"], body.content, txn_id)
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    return {
        "id": result.get("event_id"),
        "content": body.content,
        "author": {"id": user.id},
    }
