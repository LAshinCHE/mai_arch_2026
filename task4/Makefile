COMPOSE  = docker compose
APP_URL  = http://localhost:8083
SWAGGER  = http://localhost:8082
MONGO    = mongodb://localhost:27017/delivery_db
VENV     = tests/.venv

.PHONY: build up down restart logs clean mongo-shell queries test install-test test-api help

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d
	@echo "API:     $(APP_URL)"
	@echo "Swagger: $(SWAGGER)"
	@echo "MongoDB: $(MONGO)"

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

logs-app:
	$(COMPOSE) logs -f app

logs-db:
	$(COMPOSE) logs -f mongodb

clean:
	$(COMPOSE) down -v --remove-orphans

mongo-shell:
	$(COMPOSE) exec mongodb mongosh delivery_db

queries:
	mongosh $(MONGO) queries.js

test:
	@echo "=== Health check ==="
	curl -sf $(APP_URL)/ping && echo " OK"
	@echo "\n=== Create user ==="
	curl -sf -X POST $(APP_URL)/v1/users \
	  -H "Content-Type: application/json" \
	  -d '{"login":"smoketest","password":"pass","first_name":"Smoke","last_name":"Test","email":"smoke@test.com"}' \
	  | python3 -m json.tool || true
	@echo "\n=== Search by login ==="
	curl -sf "$(APP_URL)/v1/users/search?login=alice" | python3 -m json.tool || true
	@echo "\n=== Login ==="
	curl -sf -X POST $(APP_URL)/v1/auth/login \
	  -H "Content-Type: application/json" \
	  -d '{"login":"alice","password":"secret"}' \
	  | python3 -m json.tool || true

install-test:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet -r tests/requirements.txt
	@echo "Done. venv: $(VENV)"

test-api: install-test
	cd tests && ../$(VENV)/bin/python -m pytest test_api.py -v

help:
	@echo "make build        — собрать образы"
	@echo "make up           — поднять mongodb + app + swagger"
	@echo "make down         — остановить"
	@echo "make clean        — остановить + удалить volumes"
	@echo "make logs-app     — логи приложения"
	@echo "make mongo-shell  — открыть mongosh"
	@echo "make queries      — выполнить queries.js"
	@echo "make test         — smoke tests (curl)"
	@echo "make install-test — создать venv и установить зависимости"
	@echo "make test-api     — Python API тесты (pytest)"
