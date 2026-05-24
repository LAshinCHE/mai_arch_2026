# Task 4 — MongoDB: Документная модель для сервиса доставки

**Вариант 6 — Сервис доставки (CDEK-like)**

Курс: Архитектура программных систем

---

## Содержание

1. [Что сделано](#что-сделано)
2. [Быстрый старт](#быстрый-старт)
3. [Авторизация](#авторизация)
4. [Примеры запросов](#примеры-запросов)
5. [Тесты](#тесты)
6. [MongoDB: модель данных](#mongodb-модель-данных)
7. [Работа с MongoDB напрямую](#работа-с-mongodb-напрямую)
8. [Структура файлов](#структура-файлов)
9. [API эндпоинты](#api-эндпоинты)
10. [Технологии](#технологии)

---

## Что сделано

| Требование | Файл |
|---|---|
| Документная модель + обоснование embedded/references | `schema_design.md` |
| Схемы и индексы ($jsonSchema) | `validation.js` |
| Тестовые данные (12 документов в каждой коллекции) | `data.js` |
| CRUD + агрегации | `queries.js` |
| API на C++ (userver + MongoDB) | `src/` |
| Docker окружение | `docker-compose.yaml`, `Dockerfile` |
| Python API тесты (pytest) | `tests/` |

---

## Быстрый старт

```bash
# Требования: Docker >= 24, Docker Compose >= 2.20, make
cd mai_system_designed/task4

make build  # сборка C++ приложения (~2-3 мин)
make up     # поднять MongoDB + инициализация + API + Swagger
```

После запуска:
- **API**: http://localhost:8083
- **Swagger UI**: http://localhost:8082
- **MongoDB**: `mongodb://localhost:27017/delivery_db`

Порядок инициализации в docker-compose:
1. `mongodb` — стартует MongoDB 7
2. `mongo-init` — выполняет `validation.js` (создаёт коллекции с $jsonSchema) и `data.js` (загружает тестовые данные)
3. `app` — запускает C++ API только после того, как `mongo-init` завершился с кодом 0

---

## Авторизация

Большинство эндпоинтов требуют токен в заголовке `Authorization: Bearer <token>`.

### Шаг 1. Зарегистрироваться

```bash
curl -X POST http://localhost:8083/v1/users \
  -H "Content-Type: application/json" \
  -d '{"login":"newuser","password":"mypass","first_name":"Ivan","last_name":"Petrov","email":"newuser@example.com"}'
# {"id":"<24-hex-objectid>"}
```

### Шаг 2. Получить токен

```bash
curl -X POST http://localhost:8083/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"newuser","password":"mypass"}'
# {"token":"<uuid>","user_id":"<24-hex-objectid>"}
```

### Шаг 3. Использовать токен

```bash
curl http://localhost:8083/v1/users/<user_id>/packages \
  -H "Authorization: Bearer <token>"
```

### Готовые токены (из тестовых данных)

| Пользователь | Пароль | Токен |
|---|---|---|
| alice | secret | `test-token-alice` |
| bob | 12345 | `test-token-bob` |
| charlie | 1 | `test-token-charlie` |

> Пользователи `alice`–`lisa` из `data.js` уже есть в БД. Если пытаться зарегистрировать `alice` или `ivan` — получите 409.

---

## Примеры запросов

```bash
# Поиск по логину
curl "http://localhost:8083/v1/users/search?login=alice"

# Поиск по маске имени (регистронезависимо)
curl "http://localhost:8083/v1/users/search?name=Ali&last_name=Smi"

# Создать посылку
curl -X POST http://localhost:8083/v1/packages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-alice" \
  -d '{"description":"Книги","weight":2.5}'

# Посылки пользователя
curl "http://localhost:8083/v1/users/<user_id>/packages" \
  -H "Authorization: Bearer test-token-alice"

# Создать доставку
curl -X POST http://localhost:8083/v1/deliveries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-alice" \
  -d '{"sender_id":"<id>","recipient_id":"<id>","package_id":"<id>","address":"ул. Ленина, д. 1"}'

# Доставки по получателю
curl "http://localhost:8083/v1/deliveries?recipient_id=<id>" \
  -H "Authorization: Bearer test-token-alice"

# Доставки по отправителю
curl "http://localhost:8083/v1/deliveries?sender_id=<id>" \
  -H "Authorization: Bearer test-token-alice"
```

---

## Тесты

### Python API тесты

Тесты работают против живого сервера и покрывают все эндпоинты: happy path, ошибочные коды (400, 401, 409), структуру ответов.

```bash
# Установить зависимости и запустить
make test-api
```

Или вручную:

```bash
python3 -m venv tests/.venv
tests/.venv/bin/pip install -r tests/requirements.txt
cd tests && ../tests/.venv/bin/python -m pytest test_api.py -v
```

Ожидаемый вывод:

```
collected 40 items

test_api.py::test_ping PASSED
test_api.py::TestCreateUser::test_returns_201_and_object_id PASSED
test_api.py::TestCreateUser::test_duplicate_login_returns_409 PASSED
test_api.py::TestCreateUser::test_duplicate_email_returns_409 PASSED
...
test_api.py::TestGetDeliveries::test_preseeded_deliveries_exist PASSED

40 passed in 0.20s
```

**Что покрывают тесты:**

| Группа | Тестов | Сценарии |
|---|---|---|
| Health | 1 | GET /ping → 200 |
| CreateUser | 5 | 201 + ObjectId, дубль логина 409, дубль email 409, неполные поля 400 |
| Login | 7 | токен в ответе, неверный пароль 401, несуществующий логин 401, preseed alice/bob |
| SearchUsers | 7 | точный логин, не найден → `[]`, маска имени, регистронезависимость, нет параметров 400 |
| CreatePackage | 4 | 201, без токена 401, невалидный токен 401, кривой заголовок 401 |
| GetUserPackages | 5 | список, созданная посылка присутствует, поля ответа, без авторизации 401 |
| CreateDelivery | 5 | 201, без токена 401, невалидные ObjectId 400, пустое тело 400 |
| GetDeliveries | 6 | по sender_id, по recipient_id, поля ответа, нет параметров 400, без авторизации 401 |

### Smoke тесты (curl)

```bash
make test
```

---

## MongoDB: модель данных

### Коллекции

В базе `delivery_db` четыре коллекции:

| Коллекция | Назначение |
|---|---|
| `users` | Аккаунты пользователей |
| `packages` | Посылки (принадлежат владельцу `owner_id`) |
| `deliveries` | Заявки на доставку (связывают отправителя, получателя и посылку) |
| `auth_tokens` | Bearer-токены с временем жизни |

### Почему references, а не embedded

MongoDB позволяет хранить связанные данные прямо внутри документа (embedded). Для этого проекта выбраны ссылки (references через `ObjectId`) по следующим причинам:

**Посылки не вкладываются в пользователя**, потому что у одного пользователя может быть произвольное число посылок. Если вложить их в документ пользователя, размер документа станет непредсказуемым, а MongoDB ограничивает документ 16 МБ. Кроме того, посылки обновляются независимо от пользователя — при смене статуса посылки не нужно трогать документ пользователя.

**Доставки не вкладываются ни в пользователя, ни в посылку**, потому что доставка ссылается сразу на трёх участников (отправитель, получатель, посылка) и имеет собственный жизненный цикл статусов.

**Когда embedded оправдан:** история смены статусов посылки — массив `{ status, timestamp }` внутри документа `packages` подошёл бы хорошо, так как эти записи не нужны отдельно и всегда читаются вместе с посылкой. В текущей реализации статус хранится как одно поле для простоты.

### Схема и валидация

Каждая коллекция создаётся с `$jsonSchema` валидатором (`validation.js`). Пример для `users`:

```javascript
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["login", "password_hash", "first_name", "last_name", "email", "created_at"],
            properties: {
                login:         { bsonType: "string", minLength: 1, maxLength: 64, pattern: "^[a-zA-Z0-9_]+$" },
                password_hash: { bsonType: "string", minLength: 64, maxLength: 64 },
                email:         { bsonType: "string", pattern: ".+@.+" },
                created_at:    { bsonType: "date" }
            }
        }
    },
    validationLevel: "strict",
    validationAction: "error"
});
```

`validationLevel: "strict"` означает, что валидация применяется и на вставку, и на обновление. Попытка вставить документ с некорректными данными вернёт ошибку до записи на диск.

### Индексы

```javascript
// Уникальные — предотвращают дубли
db.users.createIndex({ login: 1 },  { unique: true });
db.users.createIndex({ email: 1 },  { unique: true });
db.auth_tokens.createIndex({ token: 1 }, { unique: true });

// Ускоряют частые запросы
db.users.createIndex({ first_name: 1, last_name: 1 });  // поиск по маске имени
db.packages.createIndex({ owner_id: 1 });               // посылки пользователя
db.packages.createIndex({ status: 1 });                 // фильтрация по статусу
db.deliveries.createIndex({ sender_id: 1 });
db.deliveries.createIndex({ recipient_id: 1 });
db.deliveries.createIndex({ created_at: -1 });          // сортировка по дате (новые первые)

// TTL — MongoDB сам удаляет просроченные токены
db.auth_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });
```

TTL-индекс на `expires_at` позволяет не писать фоновый cron для очистки: MongoDB периодически (раз в 60 секунд) запускает служебную задачу и удаляет документы, у которых `expires_at` меньше текущего времени. Значение `expireAfterSeconds: 0` означает "удалять ровно в момент `expires_at`", без дополнительной задержки.

### Сравнение с PostgreSQL (task3)

| Аспект | PostgreSQL (task3) | MongoDB (task4) |
|---|---|---|
| Идентификаторы | UUID (128 бит, текст) | ObjectId (96 бит, бинарный) |
| Схема | Жёсткая, ALTER TABLE | $jsonSchema, гибкая |
| Вложенность | JOIN-ы | Embedded documents / references |
| Полнотекстовый поиск | `ILIKE`, `pg_trgm` | `$regex` с флагом `i` |
| Очистка токенов | Нет встроенного механизма | TTL-индекс |
| Агрегация | SQL GROUP BY | `$group`, `$lookup`, `$unwind` |

В PostgreSQL связи между таблицами гарантируются внешними ключами на уровне движка. В MongoDB ссылочная целостность — ответственность приложения: если удалить пользователя, его посылки останутся в коллекции. Для production-системы это решается либо каскадным удалением в коде, либо хранением всего жизненного цикла сущности в одном документе.

### Агрегации

Примеры агрегационных запросов (файл `queries.js`):

```javascript
// Статистика посылок по статусам
db.packages.aggregate([
    { $group: { _id: "$status", count: { $sum: 1 } } },
    { $sort: { count: -1 } }
])

// Топ отправителей: сколько доставок у каждого
db.deliveries.aggregate([
    { $group: { _id: "$sender_id", deliveries: { $sum: 1 } } },
    { $sort: { deliveries: -1 } },
    { $limit: 5 },
    { $lookup: {
        from: "users",
        localField: "_id",
        foreignField: "_id",
        as: "user"
    }},
    { $unwind: "$user" },
    { $project: { login: "$user.login", deliveries: 1, _id: 0 } }
])

// Все посылки пользователя alice с деталями доставок
db.users.aggregate([
    { $match: { login: "alice" } },
    { $lookup: {
        from: "packages",
        localField: "_id",
        foreignField: "owner_id",
        as: "packages"
    }}
])
```

---

## Работа с MongoDB напрямую

```bash
# Открыть mongosh
make mongo-shell

# Запустить CRUD примеры
make queries
```

Полезные команды внутри `mongosh`:

```javascript
use delivery_db

// Список коллекций
show collections

// Найти пользователя (без хэша пароля)
db.users.findOne({ login: "alice" }, { password_hash: 0 })

// Посылки alice
const alice = db.users.findOne({ login: "alice" })
db.packages.find({ owner_id: alice._id })

// Активные доставки
db.deliveries.find({ status: { $in: ["pending", "in_transit"] } })

// Посмотреть индексы коллекции
db.users.getIndexes()

// Объяснение плана запроса
db.packages.find({ owner_id: alice._id }).explain("executionStats")

// Статистика БД
db.stats()
```

---

## Структура файлов

```
task4/
├── src/
│   ├── main.cpp
│   ├── auth/
│   │   ├── auth_component.cpp   — валидация Bearer-токена
│   │   └── login_handler.cpp    — POST /v1/auth/login
│   ├── users/
│   │   ├── create_user_handler.cpp   — POST /v1/users
│   │   └── search_users_handler.cpp  — GET /v1/users/search
│   ├── packages/
│   │   ├── create_package_handler.cpp      — POST /v1/packages
│   │   └── get_user_packages_handler.cpp   — GET /v1/users/{id}/packages
│   └── deliveries/
│       ├── create_delivery_handler.cpp     — POST /v1/deliveries
│       └── get_deliveries_handler.cpp      — GET /v1/deliveries
├── tests/
│   ├── conftest.py     — фикстуры pytest
│   ├── test_api.py     — 40 API тестов
│   └── requirements.txt
├── configs/
│   ├── static_config.yaml
│   ├── config_vars.yaml
│   └── dynamic_config_fallback.json
├── schema_design.md    — описание модели и обоснование embedded/references
├── validation.js       — создание коллекций с $jsonSchema + тесты валидации
├── data.js             — тестовые данные (12 документов в каждой коллекции)
├── queries.js          — CRUD операции + агрегации
├── openapi.yaml        — OpenAPI спецификация
├── Dockerfile
├── docker-compose.yaml
├── CMakeLists.txt
├── Makefile
└── README.md
```

---

## API эндпоинты

| Метод | Путь | Auth | Описание |
|---|---|---|---|
| GET | /ping | — | Health check |
| POST | /v1/users | — | Регистрация |
| POST | /v1/auth/login | — | Получить токен |
| GET | /v1/users/search?login= | — | Поиск по логину |
| GET | /v1/users/search?name=&last_name= | — | Поиск по маске имени |
| POST | /v1/packages | Bearer | Создать посылку |
| GET | /v1/users/{id}/packages | Bearer | Посылки пользователя |
| POST | /v1/deliveries | Bearer | Создать доставку |
| GET | /v1/deliveries?sender_id= | Bearer | Доставки отправителя |
| GET | /v1/deliveries?recipient_id= | Bearer | Доставки получателя |

Идентификаторы — 24-символьные hex-строки ObjectId (в отличие от UUID в task3).

---

## Технологии

| Компонент | Стек |
|---|---|
| Backend | C++17, userver framework, MongoDB driver |
| База данных | MongoDB 7 |
| Контейнеризация | Docker, Docker Compose |
| API документация | OpenAPI 3.0, Swagger UI |
| Поиск по маске | MongoDB `$regex` с флагом `i` |
| Автоудаление токенов | TTL-индекс на `expires_at` |
| Тесты | Python 3, pytest, requests |

---

## Связь с предыдущими заданиями

- **Task 1** — архитектура системы (Structurizr DSL)
- **Task 2** — REST API на C++ (userver + PostgreSQL, UUID)
- **Task 3** — схема PostgreSQL, индексы, оптимизация запросов
- **Task 4** *(этот)* — MongoDB, документная модель, C++/userver API
