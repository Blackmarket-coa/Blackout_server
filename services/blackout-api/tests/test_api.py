from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "blackout_api_test.db"
    monkeypatch.setenv("BLACKOUT_API_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("BLACKOUT_API_JWT_SECRET", "test-secret")
    monkeypatch.setenv("BLACKOUT_API_JWT_AUDIENCE", "blackout-api")
    monkeypatch.setenv("BLACKOUT_API_JWT_ISSUER", "blackout-auth")
    monkeypatch.setenv("BLACKOUT_API_RUN_MIGRATIONS", "true")

    import blackout_api.db as db
    import blackout_api.main as main

    importlib.reload(db)
    importlib.reload(main)

    with TestClient(main.app) as c:
        yield c


def _token(sub: str, *, secret: str = "test-secret", aud: str = "blackout-api", iss: str = "blackout-auth", expired: bool = False) -> str:
    now = datetime.now(timezone.utc)
    exp = now - timedelta(minutes=1) if expired else now + timedelta(minutes=30)
    payload = {"sub": sub, "exp": exp, "aud": aud, "iss": iss}
    return jwt.encode(payload, secret, algorithm="HS256")


def _headers(sub: str, *, token: str | None = None, matrix_token: str = "matrix-token") -> dict[str, str]:
    jwt_token = token or _token(sub)
    return {
        "Authorization": f"Bearer {jwt_token}",
        "X-Matrix-Access-Token": matrix_token,
    }


def test_auth_failures(client: TestClient) -> None:
    no_auth = client.get("/v1/servers/s/members")
    assert no_auth.status_code == 401

    invalid = client.get(
        "/v1/servers/s/members",
        headers={"Authorization": "Bearer not-a-token", "X-Matrix-Access-Token": "t"},
    )
    assert invalid.status_code == 401

    missing_matrix = client.get("/v1/servers/s/members", headers={"Authorization": f"Bearer {_token('u1')}"})
    assert missing_matrix.status_code == 400

    expired = client.get("/v1/servers/s/members", headers=_headers("u1", token=_token("u1", expired=True)))
    assert expired.status_code == 401


def test_happy_path_all_v1_routes_and_permissions(client: TestClient) -> None:
    owner = _headers("owner")
    member = _headers("member")

    create_server = client.post(
        "/v1/servers",
        headers=owner,
        json={"matrix_space_id": "!space:example.org", "name": "Core", "description": "d"},
    )
    assert create_server.status_code == 200
    server_id = create_server.json()["app_server_id"]

    # join existed endpoint
    join = client.post(f"/v1/servers/{server_id}/join", headers=member, json={"role": "member"})
    assert join.status_code == 200

    # new endpoint
    members = client.get(f"/v1/servers/{server_id}/members", headers=member)
    assert members.status_code == 200
    assert len(members.json()) == 2

    # permission check for patch (member should fail)
    patch_forbidden = client.patch(f"/v1/servers/{server_id}", headers=member, json={"name": "X"})
    assert patch_forbidden.status_code == 403

    patch_ok = client.patch(
        f"/v1/servers/{server_id}",
        headers=owner,
        json={"name": "Renamed", "description": "updated"},
    )
    assert patch_ok.status_code == 200
    assert patch_ok.json()["name"] == "Renamed"

    # existed endpoint create channel
    create_channel = client.post(
        f"/v1/servers/{server_id}/channels",
        headers=owner,
        json={"matrix_room_id": "!room:example.org", "kind": "text"},
    )
    assert create_channel.status_code == 200
    channel_id = create_channel.json()["app_channel_id"]

    # new endpoint get channels
    get_channels = client.get(f"/v1/servers/{server_id}/channels", headers=member)
    assert get_channels.status_code == 200
    assert get_channels.json()[0]["app_channel_id"] == channel_id

    # existed messages endpoints
    post_message = client.post(
        f"/v1/channels/{channel_id}/messages",
        headers=member,
        json={"sender_app_user_id": "member", "body": "hello"},
    )
    assert post_message.status_code == 200

    get_messages = client.get(f"/v1/channels/{channel_id}/messages", headers=member)
    assert get_messages.status_code == 200
    assert len(get_messages.json()) == 1

    # fixed endpoint
    update_role = client.put(
        f"/v1/servers/{server_id}/members/member/role",
        headers=owner,
        json={"role": "admin"},
    )
    assert update_role.status_code == 200

    # delete channel requires admin/owner
    delete_channel_forbidden = client.delete(f"/v1/channels/{channel_id}", headers=_headers("third"))
    assert delete_channel_forbidden.status_code == 403

    delete_channel = client.delete(f"/v1/channels/{channel_id}", headers=owner)
    assert delete_channel.status_code == 200

    # leave existed endpoint
    leave = client.delete(f"/v1/servers/{server_id}/leave", headers=member)
    assert leave.status_code == 200

    # delete new endpoint owner only
    delete_server_forbidden = client.delete(f"/v1/servers/{server_id}", headers=member)
    assert delete_server_forbidden.status_code == 403

    delete_server = client.delete(f"/v1/servers/{server_id}", headers=owner)
    assert delete_server.status_code == 200


def test_mapping_and_message_persistence(client: TestClient, tmp_path: Path) -> None:
    owner = _headers("owner")
    create_server = client.post(
        "/v1/servers",
        headers=owner,
        json={"matrix_space_id": "!space2:example.org", "name": "Persist", "description": "d"},
    )
    server_id = create_server.json()["app_server_id"]

    create_channel = client.post(
        f"/v1/servers/{server_id}/channels",
        headers=owner,
        json={"matrix_room_id": "!room2:example.org", "kind": "text"},
    )
    channel_id = create_channel.json()["app_channel_id"]

    client.post(
        f"/v1/channels/{channel_id}/messages",
        headers=owner,
        json={"sender_app_user_id": "owner", "body": "persisted"},
    )

    db_path = tmp_path / "blackout_api_test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        assert conn.execute(text("select count(*) from server_map")).scalar_one() == 1
        assert conn.execute(text("select count(*) from channel_map")).scalar_one() == 1
        assert conn.execute(text("select count(*) from membership_map")).scalar_one() == 1
        assert conn.execute(text("select count(*) from message")).scalar_one() == 1


def test_websocket_gateway_connect_and_broadcast(client: TestClient) -> None:
    owner = _headers("owner")
    create_server = client.post(
        "/v1/servers",
        headers=owner,
        json={"matrix_space_id": "!space3:example.org", "name": "WS", "description": "d"},
    )
    server_id = create_server.json()["app_server_id"]

    create_channel = client.post(
        f"/v1/servers/{server_id}/channels",
        headers=owner,
        json={"matrix_room_id": "!room3:example.org", "kind": "text"},
    )
    channel_id = create_channel.json()["app_channel_id"]

    with client.websocket_connect("/gateway") as ws:
        ws.send_text("hello")
        assert ws.receive_json()["type"] == "ack"

        client.post(
            f"/v1/channels/{channel_id}/messages",
            headers=owner,
            json={"sender_app_user_id": "owner", "body": "hi"},
        )
        broadcast = ws.receive_json()
        assert broadcast["type"] == "message.created"
        assert broadcast["channel_id"] == channel_id
