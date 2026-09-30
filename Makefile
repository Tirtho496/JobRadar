.PHONY: start stop logs test eval
start:
	@test -f .env || cp .env.example .env
	docker compose up --build -d
stop:
	docker compose down
logs:
	docker compose logs -f backend frontend

test:
	docker compose run --rm backend pytest -q

eval:
	curl -s -X POST -H "X-API-Key: jobradar-local" http://localhost:8080/api/model-lab/run
