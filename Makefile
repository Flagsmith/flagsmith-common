.EXPORT_ALL_VARIABLES:

DOTENV_OVERRIDE_FILE ?= .env

COMPOSE_FILE ?= docker/docker-compose.local.yml
COMPOSE_PROJECT_NAME ?= flagsmith-common

-include $(DOTENV_OVERRIDE_FILE)

.PHONY: install-packages
install-packages: ## Install all required packages
	uv sync $(or $(opts),'--all-extras')

.PHONY: install-pre-commit ## Install pre-commit hooks
install-pre-commit:
	uv run pre-commit install

.PHONY: ensure-dotenv
ensure-dotenv: ## Create an .env file suitable for running tests
	@if [ ! -f .env ]; then cp .env-ci .env; echo ".env file created from .env-ci. Please update it with your settings."; fi

.PHONY: install
install: install-packages install-pre-commit ensure-dotenv ## Ensure the environment is set up

.PHONY: lint
lint: ## Run linters
	uv run --all-extras pre-commit run --all-files

.PHONY: docker-up
docker-up: ## Start Docker containers
	docker compose up --force-recreate --remove-orphans -d
	docker compose ps

.PHONY: docker-down
docker-down: ## Stop Docker containers
	docker compose down

.PHONY: test
test: docker-up ## Run all tests
	uv run --all-extras pytest $(opts)

.PHONY: typecheck
typecheck: ## Run mypy
	uv run --all-extras mypy src tests
.PHONY: django-make-migrations
django-make-migrations:  ## Create new migrations based on the changes detected to your models
	uv run --all-extras python manage.py waitfordb
	uv run --all-extras python manage.py makemigrations $(opts)

.PHONY: django-squash-migrations
django-squash-migrations:  ## Squash migrations for apps
	uv run --all-extras python manage.py waitfordb
	uv run --all-extras python manage.py squashmigrations $(opts)

.PHONY: django-migrate
django-migrate:  ## Apply migrations to the database
	uv run --all-extras python manage.py waitfordb
	uv run --all-extras python manage.py migrate
	uv run --all-extras python manage.py createcachetable

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
