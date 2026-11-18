-- Private application schema. Supabase Auth remains independent of these legacy-compatible accounts.
CREATE SCHEMA IF NOT EXISTS expensa;
REVOKE ALL ON SCHEMA expensa FROM PUBLIC;
CREATE TABLE IF NOT EXISTS expensa.app_state (
    id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS expensa.users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1))
);
CREATE TABLE IF NOT EXISTS expensa.memberships (
    email TEXT PRIMARY KEY REFERENCES expensa.users(email),
    role TEXT NOT NULL CHECK (role IN ('admin','full_editor','full_viewer','inventory_viewer'))
);
CREATE TABLE IF NOT EXISTS expensa.email_tokens (
    hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES expensa.users(id),
    purpose TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS expensa.sessions (
    hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES expensa.users(id),
    csrf_hash TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS expensa.rate_events (key TEXT NOT NULL, at DOUBLE PRECISION NOT NULL);
CREATE TABLE IF NOT EXISTS expensa.invitations (
    hash TEXT PRIMARY KEY, email TEXT NOT NULL, role TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS rate_events_key_at_idx ON expensa.rate_events(key, at);
CREATE INDEX IF NOT EXISTS sessions_user_idx ON expensa.sessions(user_id);
CREATE INDEX IF NOT EXISTS tokens_user_purpose_idx ON expensa.email_tokens(user_id, purpose);
ALTER TABLE expensa.app_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.email_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.rate_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE expensa.invitations ENABLE ROW LEVEL SECURITY;
-- No browser policies/grants: only the server database owner connects to this private schema.
