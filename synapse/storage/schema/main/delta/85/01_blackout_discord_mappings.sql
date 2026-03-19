-- Blackout Discord-like abstraction tables
-- Maps clean user/server/channel concepts to underlying Matrix IDs

CREATE TABLE IF NOT EXISTS blackout_users (
    id              TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    display_name    TEXT,
    avatar_url      TEXT,
    matrix_user_id  TEXT NOT NULL UNIQUE,
    created_at      BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS blackout_servers (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    icon_url        TEXT,
    owner_user_id   TEXT NOT NULL,
    matrix_space_id TEXT NOT NULL UNIQUE,
    invite_code     TEXT UNIQUE,
    created_at      BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS blackout_channels (
    id              TEXT PRIMARY KEY,
    server_id       TEXT NOT NULL REFERENCES blackout_servers(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    topic           TEXT NOT NULL DEFAULT '',
    channel_type    TEXT NOT NULL DEFAULT 'text',
    position        INTEGER NOT NULL DEFAULT 0,
    matrix_room_id  TEXT NOT NULL UNIQUE,
    created_at      BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS blackout_server_members (
    server_id       TEXT NOT NULL REFERENCES blackout_servers(id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES blackout_users(id) ON DELETE CASCADE,
    role            TEXT NOT NULL DEFAULT 'member',
    joined_at       BIGINT NOT NULL,
    PRIMARY KEY (server_id, user_id)
);

CREATE INDEX IF NOT EXISTS blackout_channels_server_id ON blackout_channels(server_id);
CREATE INDEX IF NOT EXISTS blackout_server_members_user_id ON blackout_server_members(user_id);
CREATE INDEX IF NOT EXISTS blackout_servers_invite_code ON blackout_servers(invite_code);
