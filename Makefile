.EXPORT_ALL_VARIABLES:

POETRY_VERSION ?= 2.1.1

COMPOSE_FILE ?= docker/docker-compose.local.yml
COMPOSE_PROJECT_NAME ?= flagsmith-common

.PHONY: install-pip
install-pip:
	python -m pip install --upgrade pip

.PHONY: install-poetry
install-poetry:
	curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

.PHONY: install-packages
install-packages:
	poetry install --no-root $(opts)

.PHONY: install
install: install-pip install-poetry install-packages

.PHONY: lint
lint:
	poetry run pre-commit run -a

.PHONY: docker-up
docker-up:
	docker compose up --force-recreate --remove-orphans -d
	docker compose ps

.PHONY: docker-down
docker-down:
	docker compose stop

.PHONY: test
test:
	poetry run pytest $(opts)

.PHONY: typecheck
typecheck:
	poetry run mypy .

.PHONY: django-make-migrations
django-make-migrations:
	poetry run python manage.py waitfordb
	poetry run python manage.py makemigrations $(opts)

.PHONY: django-squash-migrations
django-squash-migrations:
	poetry run python manage.py waitfordb
	poetry run python manage.py squashmigrations $(opts)

.PHONY: django-migrate
django-migrate:
	poetry run python manage.py waitfordb
	poetry run python manage.py migrate
	poetry run python manage.py createcachetable
