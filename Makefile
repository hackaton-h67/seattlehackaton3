.PHONY: help install dev-install test lint format clean docker-up docker-down init-db load-data train-models

help:
	@echo "Service-Sense Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make init-db        - Initialize databases"
	@echo "  make load-data      - Load Seattle Open Data"
	@echo "  make train-models   - Train ML models"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Start all services with docker-compose"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run linting (ruff)"
	@echo "  make format         - Format code (black)"
	@echo "  make clean          - Clean up temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Start all containers"
	@echo "  make docker-down    - Stop all containers"
	@echo "  make docker-logs    - View container logs"
	@echo "  make docker-clean   - Remove all containers and volumes"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v --cov=services --cov=shared

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

lint:
	ruff check .
	mypy services/ shared/

format:
	black .
	ruff check --fix .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache .ruff_cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

init-db:
	python scripts/init_databases.py

load-data:
	python scripts/load_data.py

train-models:
	python ml/training/train_models.py

dev:
	docker-compose up

run-api:
	cd services/api-gateway && uvicorn main:app --reload --port 8000
