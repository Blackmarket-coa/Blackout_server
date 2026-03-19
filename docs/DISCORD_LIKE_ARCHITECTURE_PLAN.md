# Blackout Core — Discord-Like Architecture Plan

## Design Principle

Users should never see anything Matrix-related. No `@user:server` IDs, no room IDs, no
`/_matrix/` endpoints. The experience should feel like Discord: servers with icons in a
sidebar, channels inside servers, instant chat, clean usernames, roles like Owner/Admin/Member.

Matrix (Synapse) is the engine underneath — it handles messaging, sync, media, auth, and
presence. Two new services sit on top:

```
┌──────────────────────────────────────────┐
│  blackout-web (Vite + vanilla TS)        │  ← What users see
│  github.com/Blackmarket-coa/blackout     │
│  Element Web fork with custom ApiClient  │
└──────────────────┬───────────────────────┘
                   │ REST + WebSocket
┌──────────────────▼───────────────────────┐
│  blackout-api (FastAPI)                  │  ← Translation layer
│  services/blackout-api/ in THIS repo     │
│  Discord concepts → Matrix operations    │
└──────────┬───────────────┬───────────────┘
           │               │
┌──────────▼──────┐  ┌─────▼──────────────┐
│  PostgreSQL     │  │ Synapse (this repo) │
│  (mappings +    │  │ on :8008            │
│   Synapse data) │  │                     │
└─────────────────┘  └────────────────────┘
```

> **Note:** The frontend (`blackout-web`) is a separate repo — an Element Web fork
> with a custom vanilla TypeScript app under `apps/blackout-web/`. Its `ApiClient`
> currently calls Matrix endpoints directly. To complete the Discord-like experience,
> the ApiClient should be updated to call `blackout-api` endpoints instead.

---

## Part 1: Blackout API Service

**Location**: `services/blackout-api/`
**Stack**: Python (FastAPI) — shares the same language as Synapse, can reuse models
**Why FastAPI over Node**: Same ecosystem as Synapse, can import monetization models
directly, simpler deployment on Railway

### 1.1 Database Schema (New Tables)

These tables go in the **same PostgreSQL** instance as Synapse, under a `blackout_` prefix
to avoid conflicts. Added via a new migration in `synapse/storage/schema/main/delta/85/`.

```sql
-- Clean server (Discord "guild") abstraction
CREATE TABLE IF NOT EXISTS blackout_servers (
    id              TEXT PRIMARY KEY,          -- UUID
    name            TEXT NOT NULL,
    icon_url        TEXT,
    owner_user_id   TEXT NOT NULL,             -- blackout user ID
    matrix_space_id TEXT NOT NULL UNIQUE,      -- !space:server
    invite_code     TEXT UNIQUE,               -- vanity invite
    created_at      BIGINT NOT NULL
);

-- Channel abstraction
CREATE TABLE IF NOT EXISTS blackout_channels (
    id              TEXT PRIMARY KEY,          -- UUID
    server_id       TEXT NOT NULL REFERENCES blackout_servers(id),
    name            TEXT NOT NULL,
    topic           TEXT DEFAULT '',
    channel_type    TEXT NOT NULL DEFAULT 'text',  -- text | voice | announcement
    position        INTEGER NOT NULL DEFAULT 0,
    matrix_room_id  TEXT NOT NULL UNIQUE,      -- !room:server
    created_at      BIGINT NOT NULL
);

-- User identity abstraction
CREATE TABLE IF NOT EXISTS blackout_users (
    id              TEXT PRIMARY KEY,          -- UUID
    username        TEXT NOT NULL UNIQUE,      -- clean: "alice", not "@alice:server"
    display_name    TEXT,
    avatar_url      TEXT,
    matrix_user_id  TEXT NOT NULL UNIQUE,      -- @alice:server
    created_at      BIGINT NOT NULL
);

-- Server membership with roles
CREATE TABLE IF NOT EXISTS blackout_server_members (
    server_id       TEXT NOT NULL REFERENCES blackout_servers(id),
    user_id         TEXT NOT NULL REFERENCES blackout_users(id),
    role            TEXT NOT NULL DEFAULT 'member',  -- owner | admin | moderator | member
    joined_at       BIGINT NOT NULL,
    PRIMARY KEY (server_id, user_id)
);

-- Role → Matrix power level mapping
-- owner=100, admin=50, moderator=25, member=0
```

### 1.2 API Endpoints

**Base URL**: `https://api.blackout.example.org/v1`

#### Auth
```
POST /auth/register
  Body: { username, password, display_name? }
  → Creates blackout_users row + Matrix user via admin API
  → Returns: { user: { id, username, display_name }, token: "jwt..." }

POST /auth/login
  Body: { username, password }
  → Validates against Matrix login, issues JWT
  → Returns: { user: { id, username, display_name, avatar_url }, token }

GET  /auth/me
  Headers: Authorization: Bearer <jwt>
  → Returns: { id, username, display_name, avatar_url }
```

#### Servers
```
POST /servers
  Body: { name, icon_url? }
  → Creates Matrix Space via /_matrix/client/v3/createRoom
  → Inserts blackout_servers row
  → Creates default #general channel
  → Adds creator as owner
  → Returns: { id, name, icon_url, invite_code, channels: [...] }

GET  /servers
  → Returns all servers the user is a member of
  → Returns: [{ id, name, icon_url, unread_count }]

GET  /servers/:id
  → Returns: { id, name, icon_url, channels: [...], members: [...] }

POST /servers/:id/join
  Body: { invite_code }
  → Joins the Matrix Space + all public child rooms
  → Inserts blackout_server_members row

DELETE /servers/:id/leave
  → Leaves all rooms in the Space
  → Removes membership row
```

#### Channels
```
POST /servers/:server_id/channels
  Body: { name, type: "text"|"voice", topic? }
  → Creates Matrix Room as child of Space
  → Inserts blackout_channels row
  → Returns: { id, name, type, topic }

GET  /servers/:server_id/channels
  → Returns: [{ id, name, type, topic, position }]

DELETE /channels/:id
  → Removes Matrix Room from Space hierarchy
  → Deletes blackout_channels row
```

#### Messages
```
GET  /channels/:id/messages?before=<cursor>&limit=50
  → Proxies to /_matrix/client/v3/rooms/{room_id}/messages
  → Transforms response: strips Matrix metadata, uses clean user IDs
  → Returns: [{ id, content, author: { id, username, avatar_url }, timestamp }]

POST /channels/:id/messages
  Body: { content }
  → Sends via /_matrix/client/v3/rooms/{room_id}/send/m.room.message
  → Returns: { id, content, author, timestamp }
```

#### Members & Roles
```
GET  /servers/:id/members
  → Returns: [{ id, username, display_name, avatar_url, role, status }]

PUT  /servers/:id/members/:user_id/role
  Body: { role: "admin"|"moderator"|"member" }
  → Updates blackout_server_members.role
  → Sets Matrix power level accordingly
```

#### Real-Time (WebSocket)
```
WS /gateway
  → Proxies Matrix /sync as WebSocket events
  → Emits Discord-like events:
    - MESSAGE_CREATE { channel_id, message }
    - MESSAGE_DELETE { channel_id, message_id }
    - MEMBER_JOIN { server_id, user }
    - MEMBER_LEAVE { server_id, user_id }
    - TYPING_START { channel_id, user_id }
    - PRESENCE_UPDATE { user_id, status }
```

### 1.3 Matrix Interaction Pattern

The API service communicates with Synapse as an **admin/appservice bot**:

1. **User creation**: Uses Synapse Admin API (`/_synapse/admin/v1/register`)
2. **Room operations**: Uses Client-Server API with a service account that has admin power
3. **Sync relay**: Long-polls `/sync` on behalf of connected WebSocket clients, transforms events

```
blackout-api authenticates to Synapse using:
  - REGISTRATION_SHARED_SECRET for user registration
  - A dedicated @blackout-bot:server admin account for room operations
  - Per-user Matrix access tokens (stored encrypted) for user-specific actions
```

### 1.4 File Structure

```
services/blackout-api/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI app, startup, CORS
│   ├── config.py             # env vars, Synapse URL, DB URL
│   ├── auth/
│   │   ├── jwt.py            # JWT issue/verify
│   │   ├── dependencies.py   # get_current_user dependency
│   │   └── routes.py         # /auth/* endpoints
│   ├── servers/
│   │   ├── models.py         # Server, Channel, Member Pydantic models
│   │   ├── routes.py         # /servers/* endpoints
│   │   └── service.py        # Matrix Space operations
│   ├── channels/
│   │   ├── routes.py         # /channels/* endpoints
│   │   └── service.py        # Matrix Room operations
│   ├── messages/
│   │   ├── routes.py         # /channels/:id/messages
│   │   └── service.py        # Matrix message send/fetch
│   ├── gateway/
│   │   └── websocket.py      # WS /gateway — sync relay
│   ├── matrix/
│   │   └── client.py         # Synapse HTTP client wrapper
│   └── db/
│       ├── connection.py     # asyncpg pool
│       └── queries.py        # SQL queries for mapping tables
└── railway.toml
```

---

## Part 2: Blackout Web Frontend

**Repo**: `github.com/Blackmarket-coa/blackout`
**Location**: `apps/blackout-web/`
**Stack**: Vite + vanilla TypeScript (no React/Vue), minimal CSS

### 2.1 Current State

The frontend is a custom app with:
- `ApiClient` class that calls Matrix endpoints directly (`/_matrix/client/v3/*`)
- Tab-based navigation (auth, rooms, timeline, settings)
- Simple `setState()` pattern (no Redux/Zustand)
- Session persisted in `localStorage`
- Mock API fallback for dev/testing
- Dark theme CSS

### 2.2 What Needs to Change

The `ApiClient` in `apps/blackout-web/src/api/client.ts` should be updated to call
`blackout-api` instead of Matrix directly. The mapping:

| Current (Matrix direct)                    | New (via blackout-api)                |
|--------------------------------------------|---------------------------------------|
| `POST /_matrix/client/v3/login`            | `POST /v1/auth/login`                 |
| `GET /_matrix/client/v3/joined_rooms`      | `GET /v1/servers`                     |
| `GET /_matrix/client/v3/rooms/{id}/messages` | `GET /v1/channels/{id}/messages`    |
| (not implemented)                          | `POST /v1/auth/register`              |
| (not implemented)                          | `POST /v1/servers`                    |
| (not implemented)                          | `POST /v1/servers/{id}/channels`      |
| (not implemented)                          | `POST /v1/channels/{id}/messages`     |
| (not implemented)                          | `WS /gateway`                         |

### 2.3 Target Layout (Discord Clone)

```
┌──┬────────────┬─────────────────────────────────┐
│  │            │  # general                    ⚙ │
│  │ # general  ├─────────────────────────────────│
│S │ # voice    │                                 │
│E │ # announce │  alice: hey everyone!           │
│R │            │  bob: what's up?                │
│V │            │                                 │
│E │  MEMBERS   │                                 │
│R │  ───────── │                                 │
│  │  alice     │                                 │
│L │  bob       ├─────────────────────────────────│
│I │            │ ┌─────────────────────────────┐ │
│S │            │ │ Type a message...         ⏎ │ │
│T │            │ └─────────────────────────────┘ │
└──┴────────────┴─────────────────────────────────┘
```

The UI evolution (tabs → Discord layout) happens in the frontend repo.

### 2.4 Key Interactions

1. **Login** → `POST /v1/auth/login` → store JWT → redirect to first server
2. **Load servers** → `GET /v1/servers` → populate sidebar icons
3. **Select server** → `GET /v1/servers/:id` → load channels + members
4. **Select channel** → `GET /v1/channels/:id/messages` → load message history
5. **Send message** → `POST /v1/channels/:id/messages` → optimistic update
6. **Real-time** → `WS /gateway` → listen for MESSAGE_CREATE, update state
7. **Create server** → modal → `POST /v1/servers` → add to sidebar
8. **Create channel** → modal → `POST /v1/servers/:id/channels` → add to list

---

## Part 3: Railway Deployment

### 3.1 Services on Railway

```
┌─────────────────────────────────────────────┐
│              Railway Project                │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL  │  │  Redis               │  │
│  │  (Railway)   │  │  (Railway)           │  │
│  └──────┬───────┘  └──────┬──────────────┘  │
│         │                 │                 │
│  ┌──────▼─────────────────▼──────────────┐  │
│  │  blackout-server (this repo)          │  │
│  │  Synapse on :8008                     │  │
│  │  INTERNAL only — not public           │  │
│  └──────────────────┬────────────────────┘  │
│                     │                       │
│  ┌──────────────────▼────────────────────┐  │
│  │  blackout-api (FastAPI)               │  │
│  │  Public API on :8000                  │  │
│  │  Talks to Synapse + PostgreSQL        │  │
│  └──────────────────┬────────────────────┘  │
│                     │                       │
│  ┌──────────────────▼────────────────────┐  │
│  │  blackout-web (Next.js)               │  │
│  │  Public frontend on :3000             │  │
│  │  Talks to blackout-api only           │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 3.2 Environment Variables

**blackout-server** (existing):
```
SERVER_NAME=chat.blackout.app
DATABASE_HOST=postgres.railway.internal
DATABASE_PASSWORD=...
REDIS_HOST=redis.railway.internal
REGISTRATION_SHARED_SECRET=...
ENABLE_REGISTRATION=false
```

**blackout-api** (new):
```
DATABASE_URL=postgresql://...           # Same Postgres, separate connection
SYNAPSE_URL=http://blackout-server.railway.internal:8008
SYNAPSE_ADMIN_TOKEN=...                 # Admin account access token
REGISTRATION_SHARED_SECRET=...          # For creating Matrix users
JWT_SECRET=...                          # For issuing Blackout JWTs
CORS_ORIGINS=https://blackout.app
```

**blackout-web** (separate repo):
```
VITE_MATRIX_HOMESERVER_URL=https://api.blackout.app   # Points to blackout-api, NOT Synapse
```

### 3.3 Networking

- **blackout-server**: Internal only (no public domain). Accessible at
  `blackout-server.railway.internal:8008` from other Railway services.
- **blackout-api**: Public domain `api.blackout.app`. Talks to Synapse internally.
- **blackout-web**: Public domain `blackout.app`. Only talks to blackout-api.

Users never hit Synapse directly. All Matrix operations go through blackout-api.

---

## Part 4: Implementation Order

### Phase 1 — Foundation (get chat working)
1. ~~Create `services/blackout-api/` with FastAPI scaffold~~ DONE
2. ~~Add migration `delta/85/` with mapping tables~~ DONE
3. ~~Implement auth endpoints (register, login, me)~~ DONE
4. ~~Implement server create + list + join~~ DONE
5. ~~Implement channel create + delete~~ DONE
6. ~~Implement message send + fetch~~ DONE
7. ~~Add WebSocket gateway stub~~ DONE
8. Update frontend ApiClient to call blackout-api (in blackout repo)
9. Build Discord-like layout in frontend (in blackout repo)
10. Deploy all 3 services to Railway

### Phase 2 — Real-time + Polish
11. Add WebSocket gateway (/gateway) to API
12. Wire gateway to frontend for live messages
13. Add typing indicators
14. Add member list with online/offline status
15. Add server invite codes

### Phase 3 — Features
16. File uploads (proxy through API to Synapse media)
17. Role management UI
18. Server settings (name, icon, delete)
19. Channel reordering
20. Message editing/deletion

### Phase 4 — Advanced (from checklist section 13)
21. Voice channels (LiveKit)
22. Notifications
23. AI agents (Hermes/Ollama integration)
24. Marketplace hooks (FBM)

---

## Part 5: Role → Power Level Mapping

```
Role        Power Level   Capabilities
──────────  ───────────   ──────────────────────────────────
owner       100           Everything + delete server
admin       50            Manage channels, kick/ban, manage roles
moderator   25            Pin messages, mute users, delete messages
member      0             Send messages, react, upload files
```

Set via `PUT /_matrix/client/v3/rooms/{room_id}/state/m.room.power_levels` when
role changes occur in blackout-api.

---

## Part 6: What Already Exists (Reusable)

From this repo, the API layer can leverage:

| Existing Component | Reuse For |
|---|---|
| `synapse/monetization/` models | Subscription tiers, feature gating |
| `blackout_runtime/policy_engine.py` | Room presets (voice, forum, governance) |
| `blackout_runtime/server_semantics.py` | Channel type validation |
| `synapse/config/jwt.py` | JWT auth config (if using Synapse-side JWT) |
| `MonetizationStore` pattern | Model for mapping table queries |
| Admin API endpoints | User creation, room management |
| TURN/STUN config | Voice channel infrastructure |
| `TieredFeatureGate` | Feature access by subscription |
