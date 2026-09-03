SHELL := /bin/bash

.PHONY: init up down restart logs ps test backend-test frontend-build seed scan clean

init:
	python3 scripts/generate_env.py

up:
	docker compose up --build -d

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=150

down:
	docker compose down

restart:
	docker compose restart

test: backend-test frontend-build

backend-test:
	docker compose exec backend pytest -q

frontend-build:
	cd frontend && npm install && npm run build

seed:
	docker compose exec backend python -m app.seed

scan:
	bash scripts/run_security_scans.sh

clean:
	docker compose down -v --remove-orphans
