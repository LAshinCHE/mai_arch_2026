# Сервис доставки — REST API (Вариант 6)

Домашнее задание №2 по курсу «Архитектура программных систем».

REST API сервис доставки посылок, реализованный на C++ с использованием фреймворка [userver](https://userver.tech/).

## Стек технологий

- **Язык**: C++17
- **Фреймворк**: Yandex userver
- **База данных**: PostgreSQL 15
- **Контейнеризация**: Docker + Docker Compose

## Структура проекта

```
task2/
├── src/
│   ├── main.cpp
│   ├── auth/               # Аутентификация (компонент + хэндлер логина)
│   ├── users/              # Создание и поиск пользователей
│   ├── packages/           # Создание и получение посылок
│   └── deliveries/         # Создание и получение доставок
├── configs/
│   ├── static_config.yaml          # Конфигурация userver
│   ├── config_vars.yaml            # Переменные конфигурации
│   └── dynamic_config_fallback.json
├── schemas/postgresql/schema.sql   # Схема БД
├── openapi.yaml                    # OpenAPI 3.0 спецификация
├── Dockerfile
└── docker-compose.yaml
```

## API Endpoints

| Метод | URL | Авторизация | Описание |
|-------|-----|-------------|----------|
| POST | `/v1/users` | Нет | Создание нового пользователя |
| POST | `/v1/auth/login` | Нет | Вход в систему (получение токена) |
| GET | `/v1/users/search?login=<login>` | Нет | Поиск пользователя по логину |
| GET | `/v1/users/search?name=<name>&last_name=<last_name>` | Нет | Поиск по маске имени и фамилии |
| POST | `/v1/packages` | Да | Создание посылки |
| GET | `/v1/users/{id}/packages` | Да | Получение посылок пользователя |
| POST | `/v1/deliveries` | Да | Создание доставки |
| GET | `/v1/deliveries?sender_id=<id>` | Да | Доставки по отправителю |
| GET | `/v1/deliveries?recipient_id=<id>` | Да | Доставки по получателю |

## Аутентификация

Используется токен-based аутентификация. Токен передаётся в заголовке:
```
Authorization: Bearer <token>
```

Токен выдаётся при входе через `POST /v1/auth/login`. Токен хранится в БД и действителен 24 часа.

## Запуск

### Требования

- Docker
- Docker Compose

### Шаги

1. Перейти в директорию task2:
```bash
cd task2
```

2. Собрать и запустить:
```bash
docker compose up --build
```

> **Примечание**: первая сборка занимает 5–15 минут, так как происходит компиляция C++ кода. Последующие сборки значительно быстрее благодаря кэшированию слоёв Docker.

3. Проверить, что сервис запущен:
```bash
  curl http://localhost:8080/ping
```

## Примеры использования

### 1. Создание пользователя

```bash
curl -X POST http://localhost:8080/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "login": "alice",
    "password": "secret123",
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice@example.com"
  }'
```

Ответ (201 Created):
```json
{"id": "550e8400-e29b-41d4-a716-446655440000"}
```

### 2. Вход в систему

```bash
curl -X POST http://localhost:8080/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "alice", "password": "secret123"}'
```

Ответ (200 OK):
```json
{
  "token": "7f3d2c1a-...",
  "user_id": "550e8400-..."
}
```

Сохраните токен:
```bash
export TOKEN="7f3d2c1a-..."
export USER_ID="550e8400-..."
```

### 3. Поиск пользователя по логину

```bash
curl "http://localhost:8080/v1/users/search?login=alice"
```

### 4. Поиск по маске имени и фамилии

```bash
curl "http://localhost:8080/v1/users/search?name=Ali&last_name=Smi"
```

### 5. Создание посылки

```bash
curl -X POST http://localhost:8080/v1/packages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Книги", "weight": 2.5}'
```

Ответ (201 Created):
```json
{"id": "a1b2c3d4-..."}
```

```bash
export PACKAGE_ID="a1b2c3d4-..."
```

### 6. Получение посылок пользователя

```bash
curl "http://localhost:8080/v1/users/$USER_ID/packages" \
  -H "Authorization: Bearer $TOKEN"
```

### 7. Создание доставки

Сначала создайте второго пользователя (получателя):
```bash
curl -X POST http://localhost:8080/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "login": "bob",
    "password": "pass456",
    "first_name": "Bob",
    "last_name": "Jones",
    "email": "bob@example.com"
  }'
# Сохраните id как BOB_ID
export BOB_ID="..."
```

Создайте доставку:
```bash
curl -X POST http://localhost:8080/v1/deliveries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"sender_id\": \"$USER_ID\",
    \"recipient_id\": \"$BOB_ID\",
    \"package_id\": \"$PACKAGE_ID\",
    \"address\": \"ул. Ленина, д. 1, Москва\"
  }"
```

### 8. Получение доставок по отправителю

```bash
curl "http://localhost:8080/v1/deliveries?sender_id=$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Получение доставок по получателю

```bash
curl "http://localhost:8080/v1/deliveries?recipient_id=$BOB_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## HTTP статус-коды

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 201 | Ресурс создан |
| 400 | Ошибка в запросе (отсутствуют поля) |
| 401 | Требуется авторизация или неверные данные |
| 409 | Конфликт (например, логин уже занят) |
| 500 | Внутренняя ошибка сервера |

## Схема базы данных

```sql
delivery.users       -- пользователи
delivery.packages    -- посылки
delivery.deliveries  -- доставки
delivery.auth_tokens -- токены аутентификации (TTL 24ч)
```

## Пересборка только сервиса (без пересоздания БД)

```bash
docker compose build app
docker compose up -d app
```

## Остановка

```bash
docker compose down
# С удалением данных БД:
docker compose down -v
```
