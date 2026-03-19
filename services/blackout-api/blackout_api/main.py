from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base, ChannelMap, MembershipMap, ServerMap, engine, get_db
from .schemas import (
    ChannelCreateRequest,
    ChannelOut,
    JoinRequest,
    MembershipOut,
    MessageCreateRequest,
    RoleUpdateRequest,
    ServerPatchRequest,
)

app = FastAPI(title="Blackout API", version="0.1.0")

JWT_SECRET = os.getenv("BLACKOUT_API_JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("BLACKOUT_API_JWT_ALGORITHM", "HS256")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


class GatewayManager:
    def __init__(self) -> None:
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, payload: Dict[str, str]) -> None:
        for conn in list(self.connections):
            await conn.send_json(payload)


manager = GatewayManager()


def require_auth(
    authorization: str = Header(default="", alias="Authorization"),
    matrix_access_token: str = Header(default="", alias="X-Matrix-Access-Token"),
) -> Dict[str, str]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    if not matrix_access_token:
        raise HTTPException(status_code=400, detail="Missing X-Matrix-Access-Token")

    return {
        "sub": str(payload.get("sub", "")),
        "matrix_access_token": matrix_access_token,
    }


@app.get("/healthz")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/servers/{server_id}/members", response_model=List[MembershipOut])
def get_server_members(
    server_id: str,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> List[MembershipMap]:
    rows = db.execute(
        select(MembershipMap).where(MembershipMap.app_server_id == server_id)
    ).scalars()
    return list(rows)


@app.patch("/v1/servers/{server_id}")
def patch_server(
    server_id: str,
    patch: ServerPatchRequest,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    server = db.get(ServerMap, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    return {
        "app_server_id": server.app_server_id,
        "name": patch.name or server.app_server_id,
        "description": patch.description or "",
    }


@app.delete("/v1/servers/{server_id}")
def delete_server(
    server_id: str,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    server = db.get(ServerMap, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    db.query(ChannelMap).filter(ChannelMap.app_server_id == server_id).delete()
    db.query(MembershipMap).filter(MembershipMap.app_server_id == server_id).delete()
    db.delete(server)
    db.commit()
    return {"status": "deleted", "app_server_id": server_id}


@app.post("/v1/servers/{server_id}/join")
def join_server(
    server_id: str,
    payload: JoinRequest,
    auth: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    user_id = auth["sub"]
    if not user_id:
        raise HTTPException(status_code=400, detail="Token subject is required")

    membership = db.get(MembershipMap, {"app_server_id": server_id, "app_user_id": user_id})
    if membership is None:
        membership = MembershipMap(
            app_server_id=server_id,
            app_user_id=user_id,
            role=payload.role,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(membership)
    else:
        membership.role = payload.role

    db.commit()
    return {"status": "joined", "app_server_id": server_id, "app_user_id": user_id}


@app.delete("/v1/servers/{server_id}/leave")
def leave_server(
    server_id: str,
    auth: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    user_id = auth["sub"]
    membership = db.get(MembershipMap, {"app_server_id": server_id, "app_user_id": user_id})
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.delete(membership)
    db.commit()
    return {"status": "left", "app_server_id": server_id, "app_user_id": user_id}


@app.put("/v1/servers/{server_id}/members/{member_id}/role")
def update_member_role(
    server_id: str,
    member_id: str,
    payload: RoleUpdateRequest,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    membership = db.get(
        MembershipMap, {"app_server_id": server_id, "app_user_id": member_id}
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    membership.role = payload.role
    db.commit()
    return {"status": "updated", "app_server_id": server_id, "app_user_id": member_id}


@app.get("/v1/servers/{server_id}/channels", response_model=List[ChannelOut])
def get_server_channels(
    server_id: str,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> List[ChannelMap]:
    rows = db.execute(select(ChannelMap).where(ChannelMap.app_server_id == server_id)).scalars()
    return list(rows)


@app.post("/v1/servers/{server_id}/channels", response_model=ChannelOut)
def create_channel(
    server_id: str,
    payload: ChannelCreateRequest,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> ChannelMap:
    channel = ChannelMap(
        app_channel_id=str(uuid.uuid4()),
        matrix_room_id=payload.matrix_room_id,
        app_server_id=server_id,
        kind=payload.kind,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@app.delete("/v1/channels/{channel_id}")
def delete_channel(
    channel_id: str,
    _: Dict[str, str] = Depends(require_auth),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    channel = db.get(ChannelMap, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()
    return {"status": "deleted", "app_channel_id": channel_id}


_MESSAGES: Dict[str, List[Dict[str, str]]] = {}


@app.get("/v1/channels/{channel_id}/messages")
def get_messages(
    channel_id: str,
    _: Dict[str, str] = Depends(require_auth),
) -> Dict[str, List[Dict[str, str]]]:
    return {"items": _MESSAGES.get(channel_id, [])}


@app.post("/v1/channels/{channel_id}/messages")
async def post_message(
    channel_id: str,
    payload: MessageCreateRequest,
    _: Dict[str, str] = Depends(require_auth),
) -> Dict[str, str]:
    message = {
        "id": str(uuid.uuid4()),
        "sender_app_user_id": payload.sender_app_user_id,
        "body": payload.body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _MESSAGES.setdefault(channel_id, []).append(message)
    await manager.broadcast({"type": "message.created", "channel_id": channel_id})
    return {"status": "created", "message_id": message["id"]}


@app.websocket("/gateway")
async def gateway(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "ack"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
