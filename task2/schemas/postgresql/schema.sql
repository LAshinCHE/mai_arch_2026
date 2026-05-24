DROP SCHEMA IF EXISTS delivery CASCADE;
CREATE SCHEMA delivery;

CREATE TABLE delivery.users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    login         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_login ON delivery.users (login);
CREATE INDEX idx_users_name  ON delivery.users (first_name, last_name);

CREATE TABLE delivery.packages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID NOT NULL REFERENCES delivery.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL DEFAULT '',
    weight      NUMERIC(10,3) NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'created',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_packages_owner ON delivery.packages (owner_id);

CREATE TABLE delivery.deliveries (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id    UUID NOT NULL REFERENCES delivery.users(id),
    recipient_id UUID NOT NULL REFERENCES delivery.users(id),
    package_id   UUID NOT NULL REFERENCES delivery.packages(id),
    status       TEXT NOT NULL DEFAULT 'pending',
    address      TEXT NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deliveries_sender    ON delivery.deliveries (sender_id);
CREATE INDEX idx_deliveries_recipient ON delivery.deliveries (recipient_id);

CREATE TABLE delivery.auth_tokens (
    token      TEXT PRIMARY KEY,
    user_id    UUID NOT NULL REFERENCES delivery.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours'
);
