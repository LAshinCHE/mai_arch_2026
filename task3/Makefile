COMPOSE = docker compose
APP_URL  = http://localhost:8080
SWAGGER  = http://localhost:8081
VENV     = tests/.venv
PYTEST   = $(VENV)/bin/python -m pytest

.PHONY: build up down restart logs clean db-shell test test-py test-db test-api install-test help

## Сборка Docker-образов
build:
	$(COMPOSE) build

## Запуск всех сервисов (PostgreSQL + API + Swagger UI)
up:
	$(COMPOSE) up -d
	@echo "API:     $(APP_URL)"
	@echo "Swagger: $(SWAGGER)"

## Остановка сервисов
down:
	$(COMPOSE) down

## Перезапуск
restart: down up

## Логи всех сервисов
logs:
	$(COMPOSE) logs -f

## Логи только приложения
logs-app:
	$(COMPOSE) logs -f app

## Логи только PostgreSQL
logs-db:
	$(COMPOSE) logs -f postgres

## Консоль PostgreSQL
db-shell:
	$(COMPOSE) exec postgres psql -U delivery -d delivery_db

## Остановка и удаление volumes (полная очистка)
clean:
	$(COMPOSE) down -v --remove-orphans

## Проверка работоспособности API (smoke tests)
test:
	@echo "=== Health check ==="
	curl -sf $(APP_URL)/ping && echo " OK"

	@echo "\n=== Create user ==="
	curl -sf -X POST $(APP_URL)/v1/users \
	  -H "Content-Type: application/json" \
	  -d '{"login":"testuser","password":"pass123","first_name":"Test","last_name":"User","email":"test@test.com"}' \
	  | python3 -m json.tool || true

	@echo "\n=== Search user by login ==="
	curl -sf "$(APP_URL)/v1/users/search?login=alice" | python3 -m json.tool || true

	@echo "\n=== Search user by name mask ==="
	curl -sf "$(APP_URL)/v1/users/search?name=Ali&last_name=Smi" | python3 -m json.tool || true

	@echo "\n=== Login (get token) ==="
	curl -sf -X POST $(APP_URL)/v1/auth/login \
	  -H "Content-Type: application/json" \
	  -d '{"login":"alice","password":"secret"}' \
	  | python3 -m json.tool || true

	@echo "\n=== Get user packages (with test token) ==="
	curl -sf "$(APP_URL)/v1/users/a0000001-0000-0000-0000-000000000001/packages" \
	  -H "Authorization: Bearer test-token-alice" \
	  | python3 -m json.tool || true

	@echo "\n=== Get deliveries by sender ==="
	curl -sf "$(APP_URL)/v1/deliveries?sender_id=a0000001-0000-0000-0000-000000000001" \
	  -H "Authorization: Bearer test-token-alice" \
	  | python3 -m json.tool || true

	@echo "\n=== Get deliveries by recipient ==="
	curl -sf "$(APP_URL)/v1/deliveries?recipient_id=a0000001-0000-0000-0000-000000000002" \
	  -H "Authorization: Bearer test-token-alice" \
	  | python3 -m json.tool || true

## Создать venv и установить зависимости для Python тестов
install-test:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet -r tests/requirements.txt
	@echo "Done. venv: $(VENV)"

## Запустить все Python тесты (API + DB)
test-py: install-test
	cd tests && ../$(VENV)/bin/python -m pytest

## Только DB-тесты (не требуют запущенного API)
test-db: install-test
	cd tests && ../$(VENV)/bin/python -m pytest test_db_schema.py

## Только API-тесты (требуют make up)
test-api: install-test
	cd tests && ../$(VENV)/bin/python -m pytest test_users.py test_packages.py test_deliveries.py

## Применить только схему БД (вручную)
db-schema:
	$(COMPOSE) exec postgres psql -U delivery -d delivery_db -f /docker-entrypoint-initdb.d/01_schema.sql

## Загрузить тестовые данные вручную
db-data:
	$(COMPOSE) exec postgres psql -U delivery -d delivery_db -f /docker-entrypoint-initdb.d/02_data.sql

## Запустить queries.sql
db-queries:
	$(COMPOSE) exec -T postgres psql -U delivery -d delivery_db < queries.sql

help:
	@echo "Доступные команды:"
	@echo "  make build      — сборка образов"
	@echo "  make up         — запуск сервисов"
	@echo "  make down       — остановка сервисов"
	@echo "  make restart    — перезапуск"
	@echo "  make logs       — логи всех сервисов"
	@echo "  make logs-app   — логи приложения"
	@echo "  make logs-db    — логи PostgreSQL"
	@echo "  make db-shell   — консоль PostgreSQL"
	@echo "  make clean      — полная очистка (с volumes)"
	@echo "  make test          — smoke tests (curl)"
	@echo "  make install-test  — установить зависимости для Python тестов"
	@echo "  make test-py       — все Python тесты (API + DB)"
	@echo "  make test-db       — только DB unit-тесты"
	@echo "  make test-api      — только API integration-тесты"
	@echo "  make db-queries    — выполнить queries.sql"
