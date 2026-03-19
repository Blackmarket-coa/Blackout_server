from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.db.connection import create_pool, close_pool, get_pool
from app.matrix.client import MatrixClient
from app.auth.routes import router as auth_router
from app.servers.routes import router as servers_router
from app.channels.routes import router as channels_router
from app.messages.routes import router as messages_router
from app.gateway.websocket import router as gateway_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    await create_pool()
    pool = get_pool()
    # Ensure mapping tables exist (idempotent, matches delta/85 migration)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blackout_users (
                id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                display_name TEXT, avatar_url TEXT,
                matrix_user_id TEXT NOT NULL UNIQUE, created_at BIGINT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS blackout_servers (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, icon_url TEXT,
                owner_user_id TEXT NOT NULL, matrix_space_id TEXT NOT NULL UNIQUE,
                invite_code TEXT UNIQUE, created_at BIGINT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS blackout_channels (
                id TEXT PRIMARY KEY, server_id TEXT NOT NULL REFERENCES blackout_servers(id) ON DELETE CASCADE,
                name TEXT NOT NULL, topic TEXT NOT NULL DEFAULT '', channel_type TEXT NOT NULL DEFAULT 'text',
                position INTEGER NOT NULL DEFAULT 0, matrix_room_id TEXT NOT NULL UNIQUE,
                created_at BIGINT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS blackout_server_members (
                server_id TEXT NOT NULL REFERENCES blackout_servers(id) ON DELETE CASCADE,
                user_id TEXT NOT NULL REFERENCES blackout_users(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'member', joined_at BIGINT NOT NULL,
                PRIMARY KEY (server_id, user_id)
            );
        """)
    yield
    await close_pool()


app = FastAPI(title="Blackout API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])
app.include_router(servers_router, prefix="/v1/servers", tags=["servers"])
app.include_router(channels_router, prefix="/v1", tags=["channels"])
app.include_router(messages_router, prefix="/v1/channels", tags=["messages"])
app.include_router(gateway_router, tags=["gateway"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Matrix client singleton — used by route handlers
matrix = MatrixClient(config.SYNAPSE_URL, config.SYNAPSE_ADMIN_TOKEN)
