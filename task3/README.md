# Task 3 — Проектирование и оптимизация реляционной БД

**Вариант 6 — Сервис доставки (CDEK-like)**

Курс: Архитектура программных систем

---

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Авторизация — пошаговый пример](#авторизация--пошаговый-пример)
3. [Полный сценарий работы с API](#полный-сценарий-работы-с-api)
4. [Запуск тестов](#запуск-тестов)
5. [Справочник команд make](#справочник-команд-make)
6. [API эндпоинты](#api-эндпоинты)
7. [Схема БД](#схема-бд)
8. [Тестовые данные](#тестовые-данные)
9. [Структура файлов](#структура-файлов)
10. [Технологии](#технологии)

---

## Быстрый старт

### Требования

| Инструмент | Минимальная версия |
|---|---|
| Docker | 24 |
| Docker Compose | 2.20 |
| make | любая |
| Python + pip | 3.9+ (только для Python-тестов) |

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd mai_system_designed/task3
```

### 2. Собрать и запустить

```bash
make build   # собрать Docker-образ C++ приложения (~2 мин при первом запуске)
make up      # поднять PostgreSQL + API + Swagger UI
```

Когда команда завершится успешно, будет выведено:

```
API:     http://localhost:8080
Swagger: http://localhost:8081
```

### 3. Проверить, что всё работает

```bash
curl http://localhost:8080/ping
# Ожидаемый ответ: {"status":"ok"}
```

Или откройте **http://localhost:8081** в браузере — там интерактивная Swagger-документация со всеми эндпоинтами.

### 4. Остановить

```bash
make down    # остановить сервисы (данные в БД сохранятся)
make clean   # остановить и полностью удалить volume с данными
```

---

## Авторизация — пошаговый пример

Большинство эндпоинтов требуют заголовок `Authorization: Bearer <token>`.
Токен выдаётся при логине и действует 24 часа.

### Шаг 1. Зарегистрировать пользователя

```bash
curl -s -X POST http://localhost:8080/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "login":      "ivan",
    "password":   "mypassword",
    "first_name": "Ivan",
    "last_name":  "Petrov",
    "email":      "ivan@example.com"
  }'
```

Успешный ответ `201 Created`:

```json
{"id": "3f4e1a2b-..."}
```

Сохраните `id` — он понадобится для запросов посылок и доставок.

### Шаг 2. Войти и получить токен

```bash
curl -s -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "ivan", "password": "mypassword"}'
```

Успешный ответ `200 OK`:

```json
{
  "token":   "a1b2c3d4e5f6...",
  "user_id": "3f4e1a2b-..."
}
```

### Шаг 3. Использовать токен в запросах

Все защищённые эндпоинты принимают токен в заголовке:

```bash
curl -s http://localhost:8080/v1/users/<user_id>/packages \
  -H "Authorization: Bearer a1b2c3d4e5f6..."
```

> **Без токена или с истёкшим токеном** сервер вернёт `401 Unauthorized`.

### Готовые токены для разработки

После `make up` в БД уже есть тестовые пользователи с предустановленными токенами:

| Пользователь | Логин | Пароль | Готовый токен |
|---|---|---|---|
| Alice Smith | `alice` | `secret` | `test-token-alice` |
| Bob Johnson | `bob` | `12345` | `test-token-bob` |
| Charlie Brown | `charlie` | `1` | `test-token-charlie` |

Пример использования готового токена:

```bash
curl -s http://localhost:8080/v1/users/a0000001-0000-0000-0000-000000000001/packages \
  -H "Authorization: Bearer test-token-alice"
```

---

## Полный сценарий работы с API

Пример полного флоу: регистрация → логин → создание посылки → создание доставки.

```bash
# 1. Создать отправителя
SENDER=$(curl -s -X POST http://localhost:8080/v1/users \
  -H "Content-Type: application/json" \
  -d '{"login":"sender1","password":"pass","first_name":"Sender","last_name":"One","email":"s1@test.com"}')
SENDER_ID=$(echo $SENDER | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Создать получателя
RECIPIENT=$(curl -s -X POST http://localhost:8080/v1/users \
  -H "Content-Type: application/json" \
  -d '{"login":"recv1","password":"pass","first_name":"Recv","last_name":"One","email":"r1@test.com"}')
RECIPIENT_ID=$(echo $RECIPIENT | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 3. Войти под отправителем, получить токен
TOKEN=$(curl -s -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"sender1","password":"pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 4. Создать посылку
PACKAGE=$(curl -s -X POST http://localhost:8080/v1/packages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"description":"Ноутбук","weight":1.8}')
PACKAGE_ID=$(echo $PACKAGE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 5. Создать доставку
curl -s -X POST http://localhost:8080/v1/deliveries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"sender_id\":    \"$SENDER_ID\",
    \"recipient_id\": \"$RECIPIENT_ID\",
    \"package_id\":   \"$PACKAGE_ID\",
    \"address\":      \"ул. Ленина, д. 1, Москва\"
  }"

# 6. Посмотреть доставки отправителя
curl -s "http://localhost:8080/v1/deliveries?sender_id=$SENDER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Поиск пользователей (без токена)

```bash
# Поиск по точному логину
curl -s "http://localhost:8080/v1/users/search?login=alice"

# Поиск по маске имени и фамилии (регистронезависимо, ILIKE)
curl -s "http://localhost:8080/v1/users/search?name=Ali&last_name=Smi"
```

---

## Запуск тестов

В проекте два уровня тестов — **DB-тесты** (проверяют схему БД и SQL-ограничения напрямую через psycopg2) и **API-тесты** (интеграционные, через HTTP).

### Установить зависимости (один раз)

```bash
make install-test
# Эквивалентно: pip install -r tests/requirements.txt
# Устанавливает: pytest, pytest-order, requests, psycopg2-binary
# После установки используйте python3 -m pytest (pytest может не быть в PATH)
```

### Запустить все тесты

Перед запуском убедитесь, что сервисы подняты (`make up`).

```bash
make test-py
# Запускает: cd tests && pytest
# Покрывает: схему БД + все API эндпоинты
```

Пример вывода:

```
tests/test_db_schema.py ..........   [ 30%]
tests/test_users.py ............     [ 65%]
tests/test_packages.py ......        [ 80%]
tests/test_deliveries.py ........    [100%]
32 passed in 4.21s
```

### Запустить только DB-тесты (без запущенного API)

DB-тесты подключаются напрямую к PostgreSQL на `localhost:5432` и проверяют:
- структуру таблиц и наличие всех столбцов
- ограничения CHECK (вес, статусы, формат email)
- уникальные индексы (login, email)
- каскадное удаление (FK ON DELETE CASCADE)

```bash
make test-db
# Эквивалентно: cd tests && pytest test_db_schema.py
# Требует только запущенный PostgreSQL (make up достаточно)
```

### Запустить только API-тесты

```bash
make test-api
# Эквивалентно: cd tests && pytest test_users.py test_packages.py test_deliveries.py
# Требует полностью запущенный стек (make up)
```

### Запустить конкретный тест или класс

```bash
cd tests

# Один файл
python3 -m pytest test_users.py

# Один класс
python3 -m pytest test_users.py::TestLogin

# Один тест
python3 -m pytest test_users.py::TestLogin::test_wrong_password_returns_401

# С подробным выводом
python3 -m pytest -v test_users.py
```

### Переопределить адрес сервера или БД

По умолчанию тесты обращаются к `http://localhost:8080` и `localhost:5432`.
Можно переопределить через переменные окружения:

```bash
API_URL=http://my-server:8080 DB_CONNECTION="postgresql://..." cd tests && pytest
```

### Smoke-тесты через curl

Быстрая проверка без Python:

```bash
make test
# Выполняет набор curl-запросов: health check, создание юзера, логин,
# получение посылок и доставок — и печатает ответы через json.tool
```

---

## Справочник команд make

```
make build          — собрать Docker-образы
make up             — запустить все сервисы (postgres + app + swagger)
make down           — остановить сервисы (данные сохраняются)
make restart        — пересобрать и перезапустить
make clean          — остановить + удалить volume (полный сброс БД)

make logs           — логи всех сервисов (follow)
make logs-app       — логи только C++ приложения
make logs-db        — логи только PostgreSQL

make db-shell       — открыть psql консоль к delivery_db
make db-queries     — выполнить queries.sql (демонстрационные запросы)

make install-test   — установить Python-зависимости для тестов
make test-py        — все Python-тесты (DB + API)
make test-db        — только DB unit-тесты (только postgres)
make test-api       — только API integration-тесты (postgres + app)
make test           — smoke-тесты через curl
```

---

## API эндпоинты

| Метод | Путь | Описание | Auth |
|-------|------|----------|------|
| POST | /v1/users | Создание пользователя | — |
| POST | /v1/auth/login | Вход, получение токена | — |
| GET | /v1/users/search?login= | Поиск по точному логину | — |
| GET | /v1/users/search?name=&last_name= | Поиск по маске имени (ILIKE) | — |
| POST | /v1/packages | Создание посылки | Bearer |
| GET | /v1/users/{id}/packages | Посылки пользователя | Bearer |
| POST | /v1/deliveries | Создание доставки | Bearer |
| GET | /v1/deliveries?sender_id= | Доставки по отправителю | Bearer |
| GET | /v1/deliveries?recipient_id= | Доставки по получателю | Bearer |
| GET | /ping | Health check | — |

Интерактивная документация: **Swagger UI** → `http://localhost:8081`

---

## Схема БД

```
delivery.users
    ├── id            UUID  PK
    ├── login         TEXT  UNIQUE NOT NULL
    ├── password_hash TEXT  NOT NULL         ← SHA-256 от пароля
    ├── first_name    TEXT  NOT NULL
    ├── last_name     TEXT  NOT NULL
    ├── email         TEXT  UNIQUE NOT NULL
    └── created_at    TIMESTAMPTZ

delivery.packages
    ├── id          UUID    PK
    ├── owner_id    UUID    FK → users.id (CASCADE DELETE)
    ├── description TEXT
    ├── weight      NUMERIC(10,3)  CHECK(>= 0)
    ├── status      TEXT  CHECK('created','in_transit','delivered','cancelled')
    └── created_at  TIMESTAMPTZ

delivery.deliveries
    ├── id           UUID PK
    ├── sender_id    UUID FK → users.id
    ├── recipient_id UUID FK → users.id      ← sender_id ≠ recipient_id
    ├── package_id   UUID FK → packages.id
    ├── status       TEXT CHECK('pending','in_transit','delivered','cancelled')
    ├── address      TEXT NOT NULL
    └── created_at   TIMESTAMPTZ

delivery.auth_tokens
    ├── token      TEXT PK
    ├── user_id    UUID FK → users.id (CASCADE DELETE)
    ├── created_at TIMESTAMPTZ
    └── expires_at TIMESTAMPTZ  ← NOW() + 24h
```

---

## Тестовые данные

После `make up` БД содержит предзаполненные данные из `data.sql`:

| Таблица | Записей |
|---------|---------|
| users | 12 |
| packages | 12 |
| deliveries | 12 |
| auth_tokens | 3 |

Готовые UUID для тестирования:

| Пользователь | UUID |
|---|---|
| alice | `a0000001-0000-0000-0000-000000000001` |
| bob | `a0000001-0000-0000-0000-000000000002` |
| charlie | `a0000001-0000-0000-0000-000000000003` |

---

## Структура файлов

```
task3/
├── schemas/postgresql/
│   └── schema.sql          # DDL: CREATE TABLE + все индексы
├── src/                    # C++ исходный код (userver framework)
│   ├── auth/               # POST /v1/auth/login
│   ├── users/              # POST /v1/users, GET /v1/users/search
│   ├── packages/           # POST /v1/packages, GET /v1/users/{id}/packages
│   └── deliveries/         # POST /v1/deliveries, GET /v1/deliveries
├── tests/
│   ├── conftest.py         # Фикстуры pytest (api, db, alice_auth, ...)
│   ├── pytest.ini          # Конфигурация pytest
│   ├── requirements.txt    # pytest, requests, psycopg2-binary
│   ├── test_db_schema.py   # DB unit-тесты (constraints, indexes)
│   ├── test_users.py       # API тесты: users + login
│   ├── test_packages.py    # API тесты: packages
│   └── test_deliveries.py  # API тесты: deliveries
├── configs/                # Конфигурация userver
├── data.sql                # Тестовые данные (12 записей в каждой таблице)
├── queries.sql             # SQL запросы для всех API операций
├── optimization.md         # Анализ и оптимизация запросов (EXPLAIN)
├── openapi.yaml            # OpenAPI спецификация
├── Dockerfile              # Образ C++ приложения
├── docker-compose.yaml     # Оркестрация: postgres + app + swagger-ui
├── CMakeLists.txt          # Система сборки C++
├── Makefile                # Удобные команды
└── README.md               # Этот файл
```

---

## Технологии

| Компонент | Технология |
|-----------|-----------|
| Backend | C++ 17, userver framework |
| База данных | PostgreSQL 15 |
| Контейнеризация | Docker, Docker Compose |
| API документация | OpenAPI 3.0, Swagger UI |
| Индексы для ILIKE | pg_trgm (GIN) |
| Тесты | Python 3, pytest, psycopg2, requests |

---

## Связь с предыдущими заданиями

- **Task 1** — архитектура системы (Structurizr DSL)
- **Task 2** — реализация REST API на C++ (userver + PostgreSQL)
- **Task 3** *(этот)* — схема БД, индексы, оптимизация запросов, тестовые данные
