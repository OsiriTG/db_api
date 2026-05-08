BEGIN TRANSACTION;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chat_type') THEN
        CREATE TYPE chat_type AS ENUM ('private', 'group', 'supergroup', 'channel');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    is_bot BOOLEAN NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT DEFAULT NULL,
    username TEXT DEFAULT NULL,
    language_code TEXT DEFAULT NULL,
    is_premium BOOLEAN DEFAULT NULL,
    added_to_attachment_menu BOOLEAN DEFAULT NULL,
    can_join_groups BOOLEAN DEFAULT NULL,
    can_read_all_group_messages BOOLEAN DEFAULT NULL,
    supports_inline_queries BOOLEAN DEFAULT NULL,
    can_connect_to_business BOOLEAN DEFAULT NULL,
    has_main_web_app BOOLEAN DEFAULT NULL,
    has_topics_enabled BOOLEAN DEFAULT NULL,
    allows_users_to_create_topics BOOLEAN DEFAULT NULL,
    can_manage_bots BOOLEAN DEFAULT NULL,

    "oid" TEXT NOT NULL,
    zoneinfo TEXT DEFAULT NULL,
    date_db TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(username, "oid")
);

CREATE TABLE IF NOT EXISTS chats (
    id BIGINT PRIMARY KEY,
    "type" chat_type NOT NULL,
    title TEXT DEFAULT NULL,
    username TEXT DEFAULT NULL,
    first_name TEXT DEFAULT NULL,
    last_name TEXT DEFAULT NULL,
    is_forum BOOLEAN DEFAULT NULL,
    is_direct_messages BOOLEAN DEFAULT NULL,

    language_code TEXT DEFAULT NULL,
    "oid" TEXT NOT NULL,
    owner_id BIGINT REFERENCES users(id) ON DELETE SET NULL DEFAULT NULL,
    zoneinfo TEXT DEFAULT NULL,
    date_db TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(username, "oid")
);

CREATE TABLE IF NOT EXISTS api_keys (
    "key" TEXT PRIMARY KEY,
    permissions VARCHAR(4) NOT NULL DEFAULT '-r--',
    can_create_api_keys BOOLEAN NOT NULL DEFAULT FALSE,
    owner_id BIGINT REFERENCES users(id) ON DELETE SET NULL DEFAULT NULL,
    date_db TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_oid ON users("oid");

CREATE INDEX IF NOT EXISTS idx_chats_username ON chats(username);
CREATE INDEX IF NOT EXISTS idx_chats_owner_id ON chats(owner_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_owner_id ON api_keys(owner_id);

COMMIT;