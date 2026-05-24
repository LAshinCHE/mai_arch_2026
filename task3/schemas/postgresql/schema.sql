-- ============================================================
--  Delivery Service — Schema
--  Вариант 6: Сервис доставки (CDEK-like)
-- ============================================================

DROP SCHEMA IF EXISTS delivery CASCADE;
CREATE SCHEMA delivery;

-- ============================================================
--  Таблица пользователей
-- ============================================================
CREATE TABLE delivery.users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    login         TEXT        NOT NULL UNIQUE,
    password_hash TEXT        NOT NULL,
    first_name    TEXT        NOT NULL,
    last_name     TEXT        NOT NULL,
    email         TEXT        NOT NULL UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_login_notempty    CHECK (login <> ''),
    CONSTRAINT chk_firstname_notempty CHECK (first_name <> ''),
    CONSTRAINT chk_lastname_notempty  CHECK (last_name  <> ''),
    CONSTRAINT chk_email_format       CHECK (email LIKE '%@%')
);

-- Поиск пользователя по точному логину (API: GET /v1/users/search?login=)
CREATE UNIQUE INDEX idx_users_login
    ON delivery.users (login);

-- Поиск пользователей по маске имени и фамилии (API: GET /v1/users/search?name=&last_name=)
-- B-tree ускоряет сортировку; для паттернов %mask% дополнительно создаётся GIN/TRGM индекс ниже
CREATE INDEX idx_users_name
    ON delivery.users (first_name, last_name);

-- Ускорение поиска пользователей по маске (ILIKE '%...%') через триграммы
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_users_first_name_trgm
    ON delivery.users USING GIN (first_name gin_trgm_ops);

CREATE INDEX idx_users_last_name_trgm
    ON delivery.users USING GIN (last_name gin_trgm_ops);

-- ============================================================
--  Таблица посылок
-- ============================================================
CREATE TABLE delivery.packages (
    id          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID           NOT NULL REFERENCES delivery.users(id) ON DELETE CASCADE,
    description TEXT           NOT NULL DEFAULT '',
    weight      NUMERIC(10,3)  NOT NULL DEFAULT 0,
    status      TEXT           NOT NULL DEFAULT 'created',
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_weight_positive CHECK (weight >= 0),
    CONSTRAINT chk_status_valid    CHECK (status IN ('created', 'in_transit', 'delivered', 'cancelled'))
);

-- Получение посылок пользователя (API: GET /v1/users/{id}/packages) + FK join
CREATE INDEX idx_packages_owner
    ON delivery.packages (owner_id);

-- Фильтрация по статусу для аналитических запросов
CREATE INDEX idx_packages_status
    ON delivery.packages (status);

-- Частичный индекс для активных (не завершённых) посылок — наиболее частый случай выборки
CREATE INDEX idx_packages_owner_active
    ON delivery.packages (owner_id)
    WHERE status NOT IN ('delivered', 'cancelled');

-- ============================================================
--  Таблица доставок
-- ============================================================
CREATE TABLE delivery.deliveries (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id    UUID        NOT NULL REFERENCES delivery.users(id),
    recipient_id UUID        NOT NULL REFERENCES delivery.users(id),
    package_id   UUID        NOT NULL REFERENCES delivery.packages(id),
    status       TEXT        NOT NULL DEFAULT 'pending',
    address      TEXT        NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_delivery_status_valid CHECK (status IN ('pending', 'in_transit', 'delivered', 'cancelled')),
    CONSTRAINT chk_address_notempty      CHECK (address <> ''),
    CONSTRAINT chk_sender_ne_recipient   CHECK (sender_id <> recipient_id)
);

-- Получение доставок по отправителю (API: GET /v1/deliveries?sender_id=)
CREATE INDEX idx_deliveries_sender
    ON delivery.deliveries (sender_id);

-- Получение доставок по получателю (API: GET /v1/deliveries?recipient_id=)
CREATE INDEX idx_deliveries_recipient
    ON delivery.deliveries (recipient_id);

-- Для запросов с сортировкой по дате создания доставки
CREATE INDEX idx_deliveries_created_at
    ON delivery.deliveries (created_at DESC);

-- Покрывающий индекс для быстрой выборки по отправителю со статусом
CREATE INDEX idx_deliveries_sender_status
    ON delivery.deliveries (sender_id, status);

-- Покрывающий индекс для быстрой выборки по получателю со статусом
CREATE INDEX idx_deliveries_recipient_status
    ON delivery.deliveries (recipient_id, status);

-- ============================================================
--  Таблица токенов авторизации
-- ============================================================
CREATE TABLE delivery.auth_tokens (
    token      TEXT        PRIMARY KEY,
    user_id    UUID        NOT NULL REFERENCES delivery.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '24 hours',

    CONSTRAINT chk_token_notempty CHECK (token <> '')
);

-- Проверка токена по user_id при валидации сессий
CREATE INDEX idx_auth_tokens_user
    ON delivery.auth_tokens (user_id);

-- Индекс для фильтрации токенов по сроку действия
CREATE INDEX idx_auth_tokens_expires
    ON delivery.auth_tokens (expires_at);
