"""WebSocket gateway that relays Matrix /sync as Discord-style events.

This is a Phase 2 stub. The full implementation will:
1. Accept a WebSocket connection with a JWT token
2. Long-poll Synapse /sync on behalf of the user
3. Transform Matrix events into Discord-like events:
   - MESSAGE_CREATE { channel_id, message }
   - MESSAGE_DELETE { channel_id, message_id }
   - MEMBER_JOIN { server_id, user }
   - MEMBER_LEAVE { server_id, user_id }
   - TYPING_START { channel_id, user_id }
   - PRESENCE_UPDATE { user_id, status }
4. Send them over the WebSocket to the frontend
"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.jwt import decode_token

router = APIRouter()


@router.websocket("/gateway")
async def gateway(ws: WebSocket):
    await ws.accept()

    # Expect first message to be auth: {"token": "jwt..."}
    try:
        auth_msg = await ws.receive_text()
        data = json.loads(auth_msg)
        token = data.get("token", "")
        payload = decode_token(token)
    except Exception:
        await ws.send_json({"type": "ERROR", "detail": "Authentication required. Send {\"token\": \"...\"}."})
        await ws.close(code=4001)
        return

    await ws.send_json({
        "type": "READY",
        "user_id": payload["sub"],
    })

    # Phase 2: start /sync loop here and relay events
    # For now, keep connection alive and echo back
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)

            if data.get("type") == "PING":
                await ws.send_json({"type": "PONG"})
            else:
                await ws.send_json({"type": "ACK", "received": data.get("type", "unknown")})
    except WebSocketDisconnect:
        pass
