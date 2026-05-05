BEGIN TRANSACTION;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chat_type') THEN
        CREATE TYPE chat_type AS ENUM ('private', 'group', 'supergroup', 'channel');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    "type" chat_type NOT NULL,
    title VARCHAR(128) DEFAULT NULL,
    first_name VARCHAR(128) DEFAULT NULL,
    last_name VARCHAR(128) DEFAULT NULL,
    username VARCHAR(32) DEFAULT NULL,
    language_code VARCHAR(2) DEFAULT NULL,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    shifted_id INTEGER NOT NULL,
    "oid" TEXT NOT NULL,
    owner_id BIGINT REFERENCES users(id) ON DELETE SET NULL DEFAULT NULL,
    zoneinfo TEXT DEFAULT NULL,
    date_reg_db TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(username, shifted_id, "oid")
);

CREATE TABLE IF NOT EXISTS api_keys (
    "key" TEXT PRIMARY KEY,
    permissions VARCHAR(4) NOT NULL DEFAULT '-r--',
    can_create_api_keys BOOLEAN NOT NULL DEFAULT FALSE,
    owner_id BIGINT REFERENCES users(id) ON DELETE SET NULL DEFAULT NULL,
    date_reg TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_shifted_id ON users(shifted_id);
CREATE INDEX IF NOT EXISTS idx_users_oid ON users("oid");
CREATE INDEX IF NOT EXISTS idx_users_owner_id ON users(owner_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_owner_id ON api_keys(owner_id);

COMMIT;