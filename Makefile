.PHONY: test install uninstall up down test test-unit test-integration

install:
	docker-compose up -d
	uv pip install -e .

up:
	docker-compose up -d

down:
	docker-compose down

test:
	uv run pytest tests

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

uninstall:
	uv pip uninstall -e .
	docker-compose down
