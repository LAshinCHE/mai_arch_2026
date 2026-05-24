-- ============================================================
--  Delivery Service — SQL Queries
--  Запросы для всех API операций (Вариант 6)
-- ============================================================

-- ============================================================
--  1. Создание нового пользователя
--     API: POST /v1/users
-- ============================================================
INSERT INTO delivery.users (login, password_hash, first_name, last_name, email)
VALUES (
    'newuser',
    '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', -- sha256('password')
    'New',
    'User',
    'newuser@example.com'
)
RETURNING id::text;


-- ============================================================
--  2. Поиск пользователя по логину
--     API: GET /v1/users/search?login=alice
--     Использует: idx_users_login (unique index)
-- ============================================================
SELECT id::text, login, first_name, last_name, email
FROM delivery.users
WHERE login = 'alice';


-- ============================================================
--  3. Поиск пользователя по маске имени и фамилии
--     API: GET /v1/users/search?name=Ali&last_name=Smi
--     Использует: idx_users_first_name_trgm, idx_users_last_name_trgm (GIN)
-- ============================================================
SELECT id::text, login, first_name, last_name, email
FROM delivery.users
WHERE first_name ILIKE '%Ali%'
  AND last_name  ILIKE '%Smi%';


-- ============================================================
--  4. Создание посылки
--     API: POST /v1/packages
--     owner_id берётся из токена авторизации
-- ============================================================
INSERT INTO delivery.packages (owner_id, description, weight)
VALUES (
    'a0000001-0000-0000-0000-000000000001'::uuid,
    'Тестовая посылка',
    1.250
)
RETURNING id::text;


-- ============================================================
--  5. Получение посылок пользователя
--     API: GET /v1/users/{id}/packages
--     Использует: idx_packages_owner
-- ============================================================
SELECT id::text, owner_id::text, description, weight::text, status, created_at::text
FROM delivery.packages
WHERE owner_id = 'a0000001-0000-0000-0000-000000000001'::uuid;


-- Альтернатива с JOIN для получения информации о владельце
SELECT
    p.id::text          AS package_id,
    p.description,
    p.weight,
    p.status,
    p.created_at,
    u.login             AS owner_login,
    u.first_name || ' ' || u.last_name AS owner_name
FROM delivery.packages p
JOIN delivery.users u ON u.id = p.owner_id
WHERE p.owner_id = 'a0000001-0000-0000-0000-000000000001'::uuid;


-- ============================================================
--  6. Создание доставки от пользователя к пользователю
--     API: POST /v1/deliveries
-- ============================================================
INSERT INTO delivery.deliveries (sender_id, recipient_id, package_id, address)
VALUES (
    'a0000001-0000-0000-0000-000000000001'::uuid,
    'a0000001-0000-0000-0000-000000000002'::uuid,
    'b0000002-0000-0000-0000-000000000001'::uuid,
    'ул. Ленина, д. 10, Москва'
)
RETURNING id::text;


-- ============================================================
--  7. Получение информации о доставке по получателю
--     API: GET /v1/deliveries?recipient_id=...
--     Использует: idx_deliveries_recipient
-- ============================================================
SELECT
    id::text,
    sender_id::text,
    recipient_id::text,
    package_id::text,
    status,
    address,
    created_at::text
FROM delivery.deliveries
WHERE recipient_id = 'a0000001-0000-0000-0000-000000000002'::uuid;


-- С обогащением данными о пользователях и посылке
SELECT
    d.id::text          AS delivery_id,
    d.status,
    d.address,
    d.created_at,
    s.login             AS sender_login,
    s.first_name || ' ' || s.last_name AS sender_name,
    r.login             AS recipient_login,
    r.first_name || ' ' || r.last_name AS recipient_name,
    p.description       AS package_description,
    p.weight            AS package_weight
FROM delivery.deliveries d
JOIN delivery.users s ON s.id = d.sender_id
JOIN delivery.users r ON r.id = d.recipient_id
JOIN delivery.packages p ON p.id = d.package_id
WHERE d.recipient_id = 'a0000001-0000-0000-0000-000000000002'::uuid
ORDER BY d.created_at DESC;


-- ============================================================
--  8. Получение информации о доставке по отправителю
--     API: GET /v1/deliveries?sender_id=...
--     Использует: idx_deliveries_sender
-- ============================================================
SELECT
    id::text,
    sender_id::text,
    recipient_id::text,
    package_id::text,
    status,
    address,
    created_at::text
FROM delivery.deliveries
WHERE sender_id = 'a0000001-0000-0000-0000-000000000001'::uuid;


-- С обогащением данными о пользователях и посылке
SELECT
    d.id::text          AS delivery_id,
    d.status,
    d.address,
    d.created_at,
    s.login             AS sender_login,
    r.login             AS recipient_login,
    p.description       AS package_description,
    p.weight            AS package_weight
FROM delivery.deliveries d
JOIN delivery.users s ON s.id = d.sender_id
JOIN delivery.users r ON r.id = d.recipient_id
JOIN delivery.packages p ON p.id = d.package_id
WHERE d.sender_id = 'a0000001-0000-0000-0000-000000000001'::uuid
ORDER BY d.created_at DESC;


-- ============================================================
--  Дополнительные аналитические запросы
-- ============================================================

-- Статистика доставок по статусу
SELECT status, COUNT(*) AS cnt
FROM delivery.deliveries
GROUP BY status
ORDER BY cnt DESC;

-- Топ отправителей по количеству доставок
SELECT
    u.login,
    u.first_name || ' ' || u.last_name AS name,
    COUNT(d.id) AS deliveries_count
FROM delivery.users u
JOIN delivery.deliveries d ON d.sender_id = u.id
GROUP BY u.id, u.login, u.first_name, u.last_name
ORDER BY deliveries_count DESC
LIMIT 10;

-- Активные доставки (in_transit)
SELECT
    d.id::text,
    s.login AS sender,
    r.login AS recipient,
    d.address,
    d.created_at
FROM delivery.deliveries d
JOIN delivery.users s ON s.id = d.sender_id
JOIN delivery.users r ON r.id = d.recipient_id
WHERE d.status = 'in_transit'
ORDER BY d.created_at;
