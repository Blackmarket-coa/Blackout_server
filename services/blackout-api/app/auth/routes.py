import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app import config
from app.auth.jwt import create_token
from app.auth.dependencies import CurrentUser, get_current_user
from app.db.connection import get_pool
from app.matrix.client import MatrixClient, MatrixError

router = APIRouter()
matrix = MatrixClient(config.SYNAPSE_URL, config.SYNAPSE_ADMIN_TOKEN)


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest):
    pool = get_pool()

    # Check username not taken in our mapping
    async with pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT id FROM blackout_users WHERE username = $1", body.username)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    # Register in Synapse
    try:
        result = await matrix.register_user(body.username, body.password, config.REGISTRATION_SHARED_SECRET)
    except MatrixError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    matrix_user_id = result["user_id"]
    matrix_access_token = result["access_token"]
    user_id = str(uuid.uuid4())
    now = int(time.time() * 1000)

    # Store mapping
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO blackout_users (id, username, display_name, avatar_url, matrix_user_id, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
            user_id, body.username, body.display_name or body.username, None, matrix_user_id, now,
        )

    token = create_token(user_id, matrix_user_id, matrix_access_token)
    return AuthResponse(
        user={"id": user_id, "username": body.username, "display_name": body.display_name or body.username},
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    pool = get_pool()

    # Login via Matrix
    try:
        result = await matrix.login(body.username, body.password)
    except MatrixError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    matrix_user_id = result["user_id"]
    matrix_access_token = result["access_token"]

    # Look up our user mapping
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, username, display_name, avatar_url FROM blackout_users WHERE matrix_user_id = $1", matrix_user_id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please register first.")

    token = create_token(row["id"], matrix_user_id, matrix_access_token)
    return AuthResponse(
        user={"id": row["id"], "username": row["username"], "display_name": row["display_name"], "avatar_url": row["avatar_url"]},
        token=token,
    )


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, username, display_name, avatar_url FROM blackout_users WHERE id = $1", user.id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"id": row["id"], "username": row["username"], "display_name": row["display_name"], "avatar_url": row["avatar_url"]}
