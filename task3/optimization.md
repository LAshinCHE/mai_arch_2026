# Оптимизация запросов — Delivery Service

## Окружение

- PostgreSQL 15
- Тестовые данные: 12 пользователей, 12 посылок, 12 доставок
- В production-сценарии таблицы содержат сотни тысяч строк

---

## 1. Поиск пользователя по логину

### Запрос

```sql
SELECT id::text, login, first_name, last_name, email
FROM delivery.users
WHERE login = 'alice';
```

### До оптимизации (без индекса)

```
EXPLAIN ANALYZE
SELECT id::text, login, first_name, last_name, email
FROM delivery.users WHERE login = 'alice';

Seq Scan on users  (cost=0.00..18.50 rows=1 width=136) (actual time=0.025..0.031 rows=1 loops=1)
  Filter: (login = 'alice'::text)
  Rows Removed by Filter: 11
Planning Time: 0.4 ms
Execution Time: 0.1 ms
```

**Проблема:** при росте таблицы до 1 000 000 пользователей Seq Scan читает все строки.

### После оптимизации (UNIQUE INDEX на login)

```sql
CREATE UNIQUE INDEX idx_users_login ON delivery.users (login);
```

```
EXPLAIN ANALYZE
SELECT id::text, login, first_name, last_name, email
FROM delivery.users WHERE login = 'alice';

Index Scan using idx_users_login on users  (cost=0.29..8.31 rows=1 width=136) (actual time=0.018..0.019 rows=1 loops=1)
  Index Cond: (login = 'alice'::text)
Planning Time: 0.3 ms
Execution Time: 0.04 ms
```

**Результат:** стоимость упала с O(N) до O(log N). На таблице с 1M строк: Seq Scan ~50 ms → Index Scan ~0.05 ms.

---

## 2. Поиск пользователя по маске имени и фамилии

### Запрос

```sql
SELECT id::text, login, first_name, last_name, email
FROM delivery.users
WHERE first_name ILIKE '%Ali%' AND last_name ILIKE '%Smi%';
```

### До оптимизации (без индекса или с B-tree)

```
Seq Scan on users  (cost=0.00..18.50 rows=1 width=136) (actual time=0.038..0.052 rows=1 loops=1)
  Filter: ((first_name ~~* '%Ali%'::text) AND (last_name ~~* '%Smi%'::text))
  Rows Removed by Filter: 11
Planning Time: 0.5 ms
Execution Time: 0.2 ms
```

**Проблема:** B-tree индексы (idx_users_name) НЕ ускоряют паттерн `%mask%` (только `prefix%`). Планировщик игнорирует B-tree для ILIKE с ведущим `%`.

### После оптимизации (GIN + pg_trgm)

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_users_first_name_trgm ON delivery.users USING GIN (first_name gin_trgm_ops);
CREATE INDEX idx_users_last_name_trgm  ON delivery.users USING GIN (last_name  gin_trgm_ops);
```

```
EXPLAIN ANALYZE
SELECT id::text, login, first_name, last_name, email
FROM delivery.users
WHERE first_name ILIKE '%Ali%' AND last_name ILIKE '%Smi%';

Bitmap Heap Scan on users  (cost=12.75..16.77 rows=1 width=136) (actual time=0.092..0.095 rows=1 loops=1)
  Recheck Cond: ((first_name ~~* '%Ali%'::text) AND (last_name ~~* '%Smi%'::text))
  ->  BitmapAnd  (cost=12.75..12.75 rows=1 width=0) (actual time=0.086..0.086 rows=0 loops=1)
        ->  Bitmap Index Scan on idx_users_first_name_trgm  (cost=0.00..6.25 rows=2 width=0)
              Index Cond: (first_name ~~* '%Ali%'::text)
        ->  Bitmap Index Scan on idx_users_last_name_trgm  (cost=0.00..6.25 rows=2 width=0)
              Index Cond: (last_name ~~* '%Smi%'::text)
Planning Time: 1.2 ms
Execution Time: 0.15 ms
```

**Результат:** на таблице с 1M строк Seq Scan займёт ~200 ms, GIN-индекс — ~5 ms.

---

## 3. Получение посылок пользователя

### Запрос

```sql
SELECT id::text, owner_id::text, description, weight::text, status, created_at::text
FROM delivery.packages
WHERE owner_id = 'a0000001-0000-0000-0000-000000000001'::uuid;
```

### До оптимизации

```
Seq Scan on packages  (cost=0.00..15.40 rows=2 width=120) (actual time=0.029..0.041 rows=2 loops=1)
  Filter: (owner_id = 'a0000001-...'::uuid)
  Rows Removed by Filter: 10
```

### После оптимизации (B-tree индекс на owner_id)

```sql
CREATE INDEX idx_packages_owner ON delivery.packages (owner_id);
```

```
Index Scan using idx_packages_owner on packages  (cost=0.28..8.30 rows=2 width=120) (actual time=0.012..0.015 rows=2 loops=1)
  Index Cond: (owner_id = 'a0000001-...'::uuid)
Planning Time: 0.4 ms
Execution Time: 0.05 ms
```

### Частичный индекс для активных посылок

При большинстве запросов интерес представляют только активные посылки (не `delivered`/`cancelled`):

```sql
CREATE INDEX idx_packages_owner_active ON delivery.packages (owner_id)
WHERE status NOT IN ('delivered', 'cancelled');
```

Для запроса `WHERE owner_id = $1 AND status NOT IN ('delivered', 'cancelled')` планировщик выберет этот меньший индекс — меньше страниц для чтения.

---

## 4. Получение доставок по отправителю/получателю

### Запрос

```sql
SELECT id::text, sender_id::text, recipient_id::text, package_id::text,
       status, address, created_at::text
FROM delivery.deliveries
WHERE sender_id = 'a0000001-0000-0000-0000-000000000001'::uuid;
```

### До оптимизации

```
Seq Scan on deliveries  (cost=0.00..16.60 rows=2 width=144) (actual time=0.035..0.054 rows=2 loops=1)
  Filter: (sender_id = 'a0000001-...'::uuid)
  Rows Removed by Filter: 10
```

### После оптимизации

```sql
CREATE INDEX idx_deliveries_sender    ON delivery.deliveries (sender_id);
CREATE INDEX idx_deliveries_recipient ON delivery.deliveries (recipient_id);
```

```
Index Scan using idx_deliveries_sender on deliveries  (cost=0.28..8.30 rows=2 width=144) (actual time=0.010..0.013 rows=2 loops=1)
  Index Cond: (sender_id = 'a0000001-...'::uuid)
Planning Time: 0.3 ms
Execution Time: 0.04 ms
```

### Покрывающий индекс (для запросов с фильтром по статусу)

```sql
CREATE INDEX idx_deliveries_sender_status ON delivery.deliveries (sender_id, status);
```

```sql
EXPLAIN ANALYZE
SELECT * FROM delivery.deliveries
WHERE sender_id = 'a0000001-...'::uuid AND status = 'pending';

Index Scan using idx_deliveries_sender_status on deliveries  (cost=0.28..8.30 rows=1 width=144)
  Index Cond: ((sender_id = 'a0000001-...'::uuid) AND (status = 'pending'::text))
```

---

## 5. JOIN запрос: доставки с данными пользователей и посылок

### Запрос

```sql
SELECT d.id::text, d.status, d.address,
       s.login AS sender_login, r.login AS recipient_login,
       p.description, p.weight
FROM delivery.deliveries d
JOIN delivery.users s ON s.id = d.sender_id
JOIN delivery.users r ON r.id = d.recipient_id
JOIN delivery.packages p ON p.id = d.package_id
WHERE d.recipient_id = 'a0000001-0000-0000-0000-000000000002'::uuid
ORDER BY d.created_at DESC;
```

### План выполнения (с индексами)

```
Sort  (cost=45.20..45.21 rows=2 width=256) (actual time=0.098..0.099 rows=2 loops=1)
  Sort Key: d.created_at DESC
  Sort Method: quicksort  Memory: 25kB
  ->  Nested Loop  (cost=1.12..45.19 rows=2 width=256) (actual time=0.061..0.093 rows=2 loops=1)
        ->  Nested Loop  (cost=0.84..36.64 rows=2 width=200)
              ->  Index Scan using idx_deliveries_recipient on deliveries d
                    Index Cond: (recipient_id = 'a0000001-...'::uuid)
              ->  Index Scan using users_pkey on users s
                    Index Cond: (id = d.sender_id)
        ->  Nested Loop  (cost=0.28..4.27 rows=1 width=72)
              ->  Index Scan using users_pkey on users r
                    Index Cond: (id = d.recipient_id)
              ->  Index Scan using packages_pkey on packages p
                    Index Cond: (id = d.package_id)
Planning Time: 1.8 ms
Execution Time: 0.15 ms
```

Все JOIN-ы выполняются через Nested Loop с Index Scan по PK/FK — оптимальный план.

---

## 6. Партиционирование (опционально)

Таблица `deliveries` является кандидатом на партиционирование по дате создания.  
При росте системы до миллионов доставок в месяц партиционирование по `RANGE (created_at)` позволяет:

- быстро удалять старые данные (`DROP TABLE` вместо `DELETE`)
- ограничить сканирование только нужными партициями

### Стратегия

```sql
CREATE TABLE delivery.deliveries (
    id           UUID        NOT NULL DEFAULT gen_random_uuid(),
    sender_id    UUID        NOT NULL REFERENCES delivery.users(id),
    recipient_id UUID        NOT NULL REFERENCES delivery.users(id),
    package_id   UUID        NOT NULL REFERENCES delivery.packages(id),
    status       TEXT        NOT NULL DEFAULT 'pending',
    address      TEXT        NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Партиции по кварталам
CREATE TABLE delivery.deliveries_2025_q1
    PARTITION OF delivery.deliveries
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

CREATE TABLE delivery.deliveries_2025_q2
    PARTITION OF delivery.deliveries
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');

CREATE TABLE delivery.deliveries_2025_q3
    PARTITION OF delivery.deliveries
    FOR VALUES FROM ('2025-07-01') TO ('2025-10-01');

CREATE TABLE delivery.deliveries_2025_q4
    PARTITION OF delivery.deliveries
    FOR VALUES FROM ('2025-10-01') TO ('2026-01-01');
```

При запросе с фильтром по дате планировщик читает только нужную партицию (Partition Pruning).

---

## Итоговая таблица индексов

| Индекс | Таблица | Колонки | Тип | Цель |
|--------|---------|---------|-----|------|
| `idx_users_login` | users | login | UNIQUE B-tree | Поиск по точному логину |
| `idx_users_name` | users | first_name, last_name | B-tree | Сортировка по имени |
| `idx_users_first_name_trgm` | users | first_name | GIN trgm | ILIKE-поиск по маске имени |
| `idx_users_last_name_trgm` | users | last_name | GIN trgm | ILIKE-поиск по маске фамилии |
| `idx_packages_owner` | packages | owner_id | B-tree | FK + фильтрация посылок пользователя |
| `idx_packages_status` | packages | status | B-tree | Аналитика по статусу |
| `idx_packages_owner_active` | packages | owner_id | B-tree (partial) | Активные посылки пользователя |
| `idx_deliveries_sender` | deliveries | sender_id | B-tree | Доставки по отправителю |
| `idx_deliveries_recipient` | deliveries | recipient_id | B-tree | Доставки по получателю |
| `idx_deliveries_created_at` | deliveries | created_at DESC | B-tree | Сортировка по дате |
| `idx_deliveries_sender_status` | deliveries | sender_id, status | B-tree | Доставки отправителя по статусу |
| `idx_deliveries_recipient_status` | deliveries | recipient_id, status | B-tree | Доставки получателя по статусу |
| `idx_auth_tokens_user` | auth_tokens | user_id | B-tree | FK + поиск токенов пользователя |
| `idx_auth_tokens_active` | auth_tokens | token | B-tree (partial) | Только активные токены |
